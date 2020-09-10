# Borrowed for testing with real test data from the Vagrant project.
# https://github.com/hashicorp/vagrant

RUBY_TEST_FILES = {"file1.rb": """
require 'fileutils'
require "tempfile"

require "json"
require "log4r"

require "vagrant/box_metadata"
require "vagrant/util/downloader"
require "vagrant/util/platform"
require "vagrant/util/safe_chdir"
require "vagrant/util/subprocess"

module Vagrant
  # Represents a "box," which is a package Vagrant environment that is used
  # as a base image when creating a new guest machine.
  class Box
    include Comparable

    # Number of seconds to wait between checks for box updates
    BOX_UPDATE_CHECK_INTERVAL = 3600

    # The box name. This is the logical name used when adding the box.
    #
    # @return [String]
    attr_reader :name

    # This is the provider that this box is built for.
    #
    # @return [Symbol]
    attr_reader :provider

    # The version of this box.
    #
    # @return [String]
    attr_reader :version

    # This is the directory on disk where this box exists.
    #
    # @return [Pathname]
    attr_reader :directory

    # This is the metadata for the box. This is read from the "metadata.json"
    # file that all boxes require.
    #
    # @return [Hash]
    attr_reader :metadata

    # This is the URL to the version info and other metadata for this
    # box.
    #
    # @return [String]
    attr_reader :metadata_url

    # This is used to initialize a box.
    #
    # @param [String] name Logical name of the box.
    # @param [Symbol] provider The provider that this box implements.
    # @param [Pathname] directory The directory where this box exists on
    #   disk.
    def initialize(name, provider, version, directory, **opts)
      @name      = name
      @version   = version
      @provider  = provider
      @directory = directory
      @metadata_url = opts[:metadata_url]

      metadata_file = directory.join("metadata.json")
      raise Errors::BoxMetadataFileNotFound, name: @name if !metadata_file.file?

      begin
        @metadata = JSON.parse(directory.join("metadata.json").read)
      rescue JSON::ParserError
        raise Errors::BoxMetadataCorrupted, name: @name
      end

      @logger = Log4r::Logger.new("vagrant::box")
    end

    # This deletes the box. This is NOT undoable.
    def destroy!
      # Delete the directory to delete the box.
      FileUtils.rm_r(@directory)

      # Just return true always
      true
    rescue Errno::ENOENT
      # This means the directory didn't exist. Not a problem.
      return true
    end

    # Checks if this box is in use according to the given machine
    # index and returns the entries that appear to be using the box.
    #
    # The entries returned, if any, are not tested for validity
    # with {MachineIndex::Entry#valid?}, so the caller should do that
    # if the caller cares.
    #
    # @param [MachineIndex] index
    # @return [Array<MachineIndex::Entry>]
    def in_use?(index)
      results = []
      index.each do |entry|
        box_data = entry.extra_data["box"]
        next if !box_data

        # If all the data matches, record it
        if box_data["name"] == self.name &&
          box_data["provider"] == self.provider.to_s &&
          box_data["version"] == self.version.to_s
          results << entry
        end
      end

      return nil if results.empty?
      results
    end

    # Loads the metadata URL and returns the latest metadata associated
    # with this box.
    #
    # @param [Hash] download_options Options to pass to the downloader.
    # @return [BoxMetadata]
    def load_metadata(**download_options)
      tf = Tempfile.new("vagrant-load-metadata")
      tf.close

      url = @metadata_url
      if File.file?(url) || url !~ /^[a-z0-9]+:.*$/i
        url = File.expand_path(url)
        url = Util::Platform.cygwin_windows_path(url)
        url = "file:#{url}"
      end

      opts = { headers: ["Accept: application/json"] }.merge(download_options)
      Util::Downloader.new(url, tf.path, **opts).download!
      BoxMetadata.new(File.open(tf.path, "r"))
    rescue Errors::DownloaderError => e
      raise Errors::BoxMetadataDownloadError,
        message: e.extra_data[:message]
    ensure
      tf.unlink if tf
    end

    # Checks if the box has an update and returns the metadata, version,
    # and provider. If the box doesn't have an update that satisfies the
    # constraints, it will return nil.
    #
    # This will potentially make a network call if it has to load the
    # metadata from the network.
    #
    # @param [String] version Version constraints the update must
    #   satisfy. If nil, the version constrain defaults to being a
    #   larger version than this box.
    # @return [Array]
    def has_update?(version=nil, download_options: {})
      if !@metadata_url
        raise Errors::BoxUpdateNoMetadata, name: @name
      end

      if download_options.delete(:automatic_check) && !automatic_update_check_allowed?
        @logger.info("Skipping box update check")
        return
      end

      version += ", " if version
      version ||= ""
      version += "> #{@version}"
      md      = self.load_metadata(download_options)
      newer   = md.version(version, provider: @provider)
      return nil if !newer

      [md, newer, newer.provider(@provider)]
    end

    # Check if a box update check is allowed. Uses a file
    # in the box data directory to track when the last auto
    # update check was performed and returns true if the
    # BOX_UPDATE_CHECK_INTERVAL has passed.
    #
    # @return [Boolean]
    def automatic_update_check_allowed?
      check_path = directory.join("box_update_check")
      if check_path.exist?
        last_check_span = Time.now.to_i - check_path.mtime.to_i
        if last_check_span < BOX_UPDATE_CHECK_INTERVAL
          @logger.info("box update check is under the interval threshold")
          return false
        end
      end
      FileUtils.touch(check_path)
      true
    end

    # This repackages this box and outputs it to the given path.
    #
    # @param [Pathname] path The full path (filename included) of where
    #   to output this box.
    # @return [Boolean] true if this succeeds.
    def repackage(path)
      @logger.debug("Repackaging box '#{@name}' to: #{path}")

      Util::SafeChdir.safe_chdir(@directory) do
        # Find all the files in our current directory and tar it up!
        files = Dir.glob(File.join(".", "**", "*")).select { |f| File.file?(f) }

        # Package!
        Util::Subprocess.execute("bsdtar", "-czf", path.to_s, *files)
      end

      @logger.info("Repackaged box '#{@name}' successfully: #{path}")

      true
    end

    # Implemented for comparison with other boxes. Comparison is
    # implemented by comparing names and providers.
    def <=>(other)
      return super if !other.is_a?(self.class)

      # Comparison is done by composing the name and provider
      "#{@name}-#{@version}-#{@provider}" <=>
      "#{other.name}-#{other.version}-#{other.provider}"
    end
  end
end
""", "file2.rb": """
require 'log4r'

require 'vagrant/action/hook'
require 'vagrant/util/busy'
require 'vagrant/util/experimental'

module Vagrant
  module Action
    class Runner
      @@reported_interrupt = false

      def initialize(globals=nil, &block)
        @globals      = globals || {}
        @lazy_globals = block
        @logger       = Log4r::Logger.new("vagrant::action::runner")
      end

      def run(callable_id, options=nil)
        callable = callable_id
        if !callable.kind_of?(Builder)
          if callable_id.kind_of?(Class) || callable_id.respond_to?(:call)
            callable = Builder.build(callable_id)
          end
        end

        if !callable || !callable.respond_to?(:call)
          raise ArgumentError,
            "Argument to run must be a callable object or registered action."
        end

        # Create the initial environment with the options given
        environment = {}
        environment.merge!(@globals)
        environment.merge!(@lazy_globals.call) if @lazy_globals
        environment.merge!(options || {})

        if Vagrant::Util::Experimental.feature_enabled?("typed_triggers")
          # NOTE: Triggers are initialized later in the Action::Runer because of
          # how `@lazy_globals` are evaluated. Rather than trying to guess where
          # the `env` is coming from, we can wait until they're merged into a single
          # hash above.
          env = environment[:env]
          machine = environment[:machine]
          machine_name = machine.name if machine

          ui = Vagrant::UI::Prefixed.new(env.ui, "vagrant")
          triggers = Vagrant::Plugin::V2::Trigger.new(env, env.vagrantfile.config.trigger, machine, ui)
        end

        # Setup the action hooks
        hooks = Vagrant.plugin("2").manager.action_hooks(environment[:action_name])
        if !hooks.empty?
          @logger.info("Preparing hooks for middleware sequence...")
          environment[:action_hooks] = hooks.map do |hook_proc|
            Hook.new.tap do |h|
              hook_proc.call(h)
            end
          end

          @logger.info("#{environment[:action_hooks].length} hooks defined.")
        end

        # Run the action chain in a busy block, marking the environment as
        # interrupted if a SIGINT occurs, and exiting cleanly once the
        # chain has been run.
        ui = environment[:ui] if environment.key?(:ui)
        int_callback = lambda do
          if environment[:interrupted]
            if ui
              begin
                ui.error I18n.t("vagrant.actions.runner.exit_immediately")
              rescue ThreadError
                # We're being called in a trap-context. Wrap in a thread.
                Thread.new {
                  ui.error I18n.t("vagrant.actions.runner.exit_immediately")
                }.join(THREAD_MAX_JOIN_TIMEOUT)
              end
            end
            abort
          end

          if ui && !@@reported_interrupt
            begin
              ui.warn I18n.t("vagrant.actions.runner.waiting_cleanup")
            rescue ThreadError
              # We're being called in a trap-context. Wrap in a thread.
              Thread.new {
                ui.warn I18n.t("vagrant.actions.runner.waiting_cleanup")
              }.join(THREAD_MAX_JOIN_TIMEOUT)
            end
          end
          environment[:interrupted] = true
          @@reported_interrupt = true
        end

        action_name = environment[:action_name]

        triggers.fire_triggers(action_name, :before, machine_name, :hook) if Vagrant::Util::Experimental.feature_enabled?("typed_triggers")

        # We place a process lock around every action that is called
        @logger.info("Running action: #{environment[:action_name]} #{callable_id}")
        Util::Busy.busy(int_callback) { callable.call(environment) }

        triggers.fire_triggers(action_name, :after, machine_name, :hook) if Vagrant::Util::Experimental.feature_enabled?("typed_triggers")

        # Return the environment in case there are things in there that
        # the caller wants to use.
        environment
      end
    end
  end
end
"""}
