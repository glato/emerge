# Borrowed for testing with real test data from https://github.com/nvbn/thefuck

PYTHON_TEST_FILES = {"types.py": """
from imp import load_source
import os
import sys
from . import logs
from .shells import shell
from .conf import settings
from .const import DEFAULT_PRIORITY, ALL_ENABLED
from .exceptions import EmptyCommand
from .utils import get_alias, format_raw_script
from .output_readers import get_output


class Command(object):
    \"""Command that should be fixed.\"""

    def __init__(self, script, output):
        \"""Initializes command with given values.
        :type script: basestring
        :type output: basestring
        \"""
        self.script = script
        self.output = output

    @property
    def stdout(self):
        logs.warn('`stdout` is deprecated, please use `output` instead')
        return self.output

    @property
    def stderr(self):
        logs.warn('`stderr` is deprecated, please use `output` instead')
        return self.output

    @property
    def script_parts(self):
        if not hasattr(self, '_script_parts'):
            try:
                self._script_parts = shell.split_command(self.script)
            except Exception:
                logs.debug(u"Can't split command script {} because:\n {}".format(
                    self, sys.exc_info()))
                self._script_parts = []

        return self._script_parts

    def __eq__(self, other):
        if isinstance(other, Command):
            return (self.script, self.output) == (other.script, other.output)
        else:
            return False

    def __repr__(self):
        return u'Command(script={}, output={})'.format(
            self.script, self.output)

    def update(self, **kwargs):
        \"""Returns new command with replaced fields.
        :rtype: Command
        \"""
        kwargs.setdefault('script', self.script)
        kwargs.setdefault('output', self.output)
        return Command(**kwargs)

    @classmethod
    def from_raw_script(cls, raw_script):
        \"""Creates instance of `Command` from a list of script parts.
        :type raw_script: [basestring]
        :rtype: Command
        :raises: EmptyCommand
        \"""
        script = format_raw_script(raw_script)
        if not script:
            raise EmptyCommand

        expanded = shell.from_shell(script)
        output = get_output(script, expanded)
        return cls(expanded, output)


class Rule(object):
    \"""Rule for fixing commands.\"""

    def __init__(self, name, match, get_new_command,
                 enabled_by_default, side_effect,
                 priority, requires_output):
        \"""Initializes rule with given fields.
        :type name: basestring
        :type match: (Command) -> bool
        :type get_new_command: (Command) -> (basestring | [basestring])
        :type enabled_by_default: boolean
        :type side_effect: (Command, basestring) -> None
        :type priority: int
        :type requires_output: bool
        \"""
        self.name = name
        self.match = match
        self.get_new_command = get_new_command
        self.enabled_by_default = enabled_by_default
        self.side_effect = side_effect
        self.priority = priority
        self.requires_output = requires_output

    def __eq__(self, other):
        if isinstance(other, Rule):
            return ((self.name, self.match, self.get_new_command,
                     self.enabled_by_default, self.side_effect,
                     self.priority, self.requires_output)
                    == (other.name, other.match, other.get_new_command,
                        other.enabled_by_default, other.side_effect,
                        other.priority, other.requires_output))
        else:
            return False

    def __repr__(self):
        return 'Rule(name={}, match={}, get_new_command={}, ' \
               'enabled_by_default={}, side_effect={}, ' \
               'priority={}, requires_output={})'.format(
                   self.name, self.match, self.get_new_command,
                   self.enabled_by_default, self.side_effect,
                   self.priority, self.requires_output)

    @classmethod
    def from_path(cls, path):
        \"""Creates rule instance from path.
        :type path: pathlib.Path
        :rtype: Rule
        \"""
        name = path.name[:-3]
        if name in settings.exclude_rules:
            logs.debug(u'Ignoring excluded rule: {}'.format(name))
            return
        with logs.debug_time(u'Importing rule: {};'.format(name)):
            try:
                rule_module = load_source(name, str(path))
            except Exception:
                logs.exception(u"Rule {} failed to load".format(name), sys.exc_info())
                return
        priority = getattr(rule_module, 'priority', DEFAULT_PRIORITY)
        return cls(name, rule_module.match,
                   rule_module.get_new_command,
                   getattr(rule_module, 'enabled_by_default', True),
                   getattr(rule_module, 'side_effect', None),
                   settings.priority.get(name, priority),
                   getattr(rule_module, 'requires_output', True))

    @property
    def is_enabled(self):
        \"""Returns `True` when rule enabled.
        :rtype: bool
        \"""
        return (
            self.name in settings.rules
            or self.enabled_by_default
            and ALL_ENABLED in settings.rules
        )

    def is_match(self, command):
        \"""Returns `True` if rule matches the command.
        :type command: Command
        :rtype: bool
        \"""
        if command.output is None and self.requires_output:
            return False

        try:
            with logs.debug_time(u'Trying rule: {};'.format(self.name)):
                if self.match(command):
                    return True
        except Exception:
            logs.rule_failed(self, sys.exc_info())

    def get_corrected_commands(self, command):
        \"""Returns generator with corrected commands.
        :type command: Command
        :rtype: Iterable[CorrectedCommand]
        \"""
        new_commands = self.get_new_command(command)
        if not isinstance(new_commands, list):
            new_commands = (new_commands,)
        for n, new_command in enumerate(new_commands):
            yield CorrectedCommand(script=new_command,
                                   side_effect=self.side_effect,
                                   priority=(n + 1) * self.priority)


class CorrectedCommand(object):
    \"""Corrected by rule command.\"""

    def __init__(self, script, side_effect, priority):
        \"""Initializes instance with given fields.
        :type script: basestring
        :type side_effect: (Command, basestring) -> None
        :type priority: int
        \"""
        self.script = script
        self.side_effect = side_effect
        self.priority = priority

    def __eq__(self, other):
        \"""Ignores `priority` field.\"""
        if isinstance(other, CorrectedCommand):
            return (other.script, other.side_effect) == \
                   (self.script, self.side_effect)
        else:
            return False

    def __hash__(self):
        return (self.script, self.side_effect).__hash__()

    def __repr__(self):
        return u'CorrectedCommand(script={}, side_effect={}, priority={})'.format(
            self.script, self.side_effect, self.priority)

    def _get_script(self):
        \"""Returns fixed commands script.
        If `settings.repeat` is `True`, appends command with second attempt
        of running fuck in case fixed command fails again.
        \"""
        if settings.repeat:
            repeat_fuck = '{} --repeat {}--force-command {}'.format(
                get_alias(),
                '--debug ' if settings.debug else '',
                shell.quote(self.script))
            return shell.or_(self.script, repeat_fuck)
        else:
            return self.script

    def run(self, old_cmd):
        \"""Runs command from rule for passed command.
        :type old_cmd: Command
        \"""
        if self.side_effect:
            self.side_effect(old_cmd, self.script)
        if settings.alter_history:
            shell.put_to_history(self.script)
        # This depends on correct setting of PYTHONIOENCODING by the alias:
        logs.debug(u'PYTHONIOENCODING: {}'.format(
            os.environ.get('PYTHONIOENCODING', '!!not-set!!')))

        sys.stdout.write(self._get_script())
""", "conf.py": """
from imp import load_source
import os
import sys
from warnings import warn
from six import text_type
from . import const
from .system import Path


class Settings(dict):
    def __getattr__(self, item):
        return self.get(item)

    def __setattr__(self, key, value):
        self[key] = value

    def init(self, args=None):
        \"""Fills `settings` with values from `settings.py` and env.\"""
        from .logs import exception

        self._setup_user_dir()
        self._init_settings_file()

        try:
            self.update(self._settings_from_file())
        except Exception:
            exception("Can't load settings from file", sys.exc_info())

        try:
            self.update(self._settings_from_env())
        except Exception:
            exception("Can't load settings from env", sys.exc_info())

        self.update(self._settings_from_args(args))

    def _init_settings_file(self):
        settings_path = self.user_dir.joinpath('settings.py')
        if not settings_path.is_file():
            with settings_path.open(mode='w') as settings_file:
                settings_file.write(const.SETTINGS_HEADER)
                for setting in const.DEFAULT_SETTINGS.items():
                    settings_file.write(u'# {} = {}\n'.format(*setting))

    def _get_user_dir_path(self):
        \"""Returns Path object representing the user config resource\"""
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME', '~/.config')
        user_dir = Path(xdg_config_home, 'thefuck').expanduser()
        legacy_user_dir = Path('~', '.thefuck').expanduser()

        # For backward compatibility use legacy '~/.thefuck' if it exists:
        if legacy_user_dir.is_dir():
            warn(u'Config path {} is deprecated. Please move to {}'.format(
                legacy_user_dir, user_dir))
            return legacy_user_dir
        else:
            return user_dir

    def _setup_user_dir(self):
        \"""Returns user config dir, create it when it doesn't exist.\"""
        user_dir = self._get_user_dir_path()

        rules_dir = user_dir.joinpath('rules')
        if not rules_dir.is_dir():
            rules_dir.mkdir(parents=True)
        self.user_dir = user_dir

    def _settings_from_file(self):
        \"""Loads settings from file.\"""
        settings = load_source(
            'settings', text_type(self.user_dir.joinpath('settings.py')))
        return {key: getattr(settings, key)
                for key in const.DEFAULT_SETTINGS.keys()
                if hasattr(settings, key)}

    def _rules_from_env(self, val):
        \"""Transforms rules list from env-string to python.\"""
        val = val.split(':')
        if 'DEFAULT_RULES' in val:
            val = const.DEFAULT_RULES + [rule for rule in val if rule != 'DEFAULT_RULES']
        return val

    def _priority_from_env(self, val):
        \"""Gets priority pairs from env.\"""
        for part in val.split(':'):
            try:
                rule, priority = part.split('=')
                yield rule, int(priority)
            except ValueError:
                continue

    def _val_from_env(self, env, attr):
        \"""Transforms env-strings to python.\"""
        val = os.environ[env]
        if attr in ('rules', 'exclude_rules'):
            return self._rules_from_env(val)
        elif attr == 'priority':
            return dict(self._priority_from_env(val))
        elif attr in ('wait_command', 'history_limit', 'wait_slow_command',
                      'num_close_matches'):
            return int(val)
        elif attr in ('require_confirmation', 'no_colors', 'debug',
                      'alter_history', 'instant_mode'):
            return val.lower() == 'true'
        elif attr == 'slow_commands':
            return val.split(':')
        else:
            return val

    def _settings_from_env(self):
        \"""Loads settings from env.\"""
        return {attr: self._val_from_env(env, attr)
                for env, attr in const.ENV_TO_ATTR.items()
                if env in os.environ}

    def _settings_from_args(self, args):
        \"""Loads settings from args.\"""
        if not args:
            return {}

        from_args = {}
        if args.yes:
            from_args['require_confirmation'] = not args.yes
        if args.debug:
            from_args['debug'] = args.debug
        if args.repeat:
            from_args['repeat'] = args.repeat
        return from_args


settings = Settings(const.DEFAULT_SETTINGS)
"""}
