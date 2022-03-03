"""
Defines Configuration, YamlLoader and relevant Enums, which parses and validates a given yaml config.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import List, Dict, Optional
from enum import Enum, unique, auto

import logging
import os
import argparse
import re
import pathlib
import shutil
import yaml

import coloredlogs

from emerge.metrics.numberofmethods.numberofmethods import NumberOfMethodsMetric
from emerge.metrics.sloc.sloc import SourceLinesOfCodeMetric
from emerge.metrics.faninout.faninout import FanInOutMetric
from emerge.metrics.modularity.modularity import LouvainModularityMetric
from emerge.metrics.tfidf.tfidf import TFIDFMetric

from emerge.graph import GraphType
from emerge.log import Logger
from emerge.analysis import Analysis


LOGGER = Logger(logging.getLogger('config'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class EnumKeyValid:
    """Helper class that simply checks if a the subclassing class contains a specific key."""

    @classmethod
    def valid(cls, key) -> bool:
        if hasattr(cls, key.upper()):
            return True
        else:
            return False


@unique
class ConfigKeyProject(EnumKeyValid, Enum):
    """Config key checks of the project level."""
    PROJECT_NAME = auto()
    LOGLEVEL = auto()
    ANALYSES = auto()


@unique
class ConfigValProject(EnumKeyValid, Enum):
    """Config value checks of the project level."""
    DEBUG = auto()
    INFO = auto()
    ERROR = auto()


@unique
class ConfigKeyAnalysis(EnumKeyValid, Enum):
    """Config key checks of the analysis level."""
    ANALYSIS_NAME = auto()
    SOURCE_DIRECTORY = auto()
    ONLY_PERMIT_LANGUAGES = auto()
    ONLY_PERMIT_FILE_EXTENSIONS = auto()
    IGNORE_DIRECTORIES_CONTAINING = auto()
    IGNORE_FILES_CONTAINING = auto()
    IGNORE_DEPENDENCIES_CONTAINING = auto()
    IMPORT_ALIASES = auto()
    FILE_SCAN = auto()
    ENTITY_SCAN = auto()
    EXPORT = auto()


@unique
class ConfigKeyFileScan(EnumKeyValid, Enum):
    """Config key checks of the file scan level."""
    NUMBER_OF_METHODS = auto()
    SOURCE_LINES_OF_CODE = auto()
    DEPENDENCY_GRAPH = auto()
    FAN_IN_OUT = auto()
    LOUVAIN_MODULARITY = auto()
    TFIDF = auto()


@unique
class ConfigKeyEntityScan(EnumKeyValid, Enum):
    """Config key checks of the entity scan level."""
    NUMBER_OF_METHODS = auto()
    SOURCE_LINES_OF_CODE = auto()
    NUMBER_OF_ENTITIES = auto()
    DEPENDENCY_GRAPH = auto()
    INHERITANCE_GRAPH = auto()
    COMPLETE_GRAPH = auto()
    FAN_IN_OUT = auto()
    LOUVAIN_MODULARITY = auto()
    TFIDF = auto()


@unique
class ConfigKeyExport(EnumKeyValid, Enum):
    """Config key checks of the export level."""
    DIRECTORY = auto()
    GRAPHML = auto()
    DOT = auto()
    TABULAR_FILE = auto()
    TABULAR_CONSOLE = auto()
    TABULAR_CONSOLE_OVERALL = auto()
    JSON = auto()
    D3 = auto()


class Configuration:
    def __init__(self, version: str):
        """Reads, validates and contains the current configuration."""
        self.analyses: List[Analysis] = []
        self.project_name: str = "unnamed"
        self._yaml_loader: YamlLoader = YamlLoader()
        self.yaml_config_path = ""
        self.valid = False
        self.version = version
        self.arg_parser = None
        self.supported_languages = List[str]

    def _get_own__dict__(self):
        return self.__dict__

    def setup_commang_line_arguments(self) -> None:
        """Setup command line arguments."""
        self.arg_parser = argparse.ArgumentParser(description='🔎 Welcome to emerge ' + f'{self.version}')
        self.arg_parser.add_argument('-c', '--config', dest='yamlconfig', help='set yaml config file')
        self.arg_parser.add_argument('-v', '--verbose', dest='verbose', help='set logging level to INFO', action='store_true')
        self.arg_parser.add_argument('-d', '--debug', dest='debug', help='set logging level to DEBUG', action='store_true')
        self.arg_parser.add_argument('-e', '--error', dest='error', help='set logging level to ERROR', action='store_true')
        self.arg_parser.add_argument('-a', '--add-config', dest='language', help='add a new config from a template, where LANGUAGE is one of [' + ", ".join(self.supported_languages) + ']')

    def _options_for_value(self, value: str) -> Optional[List]:
        """Checks if a configuration value has options and returns them.

        Args:
            value (str): A given configuration value.

        Returns:
            Optional[List]: Returns a list of options if present, otherwise None.
        """
        match = re.search(r"(.+)\((.*)\)$", value)
        if match:
            options = match.group(2)
            if not bool(options):
                return None
            else:
                return [s.strip() for s in options.split(',')]
        return None

    def parse_args(self) -> None:
        """Parses the command line arguments."""
        args = self.arg_parser.parse_args()
        no_arguments = all((v == False or v == None) for v in vars(args).values())

        if no_arguments:
            self.arg_parser.print_help()
            return

        if args.language:
            here = pathlib.Path(__file__).parent
            config_file = here.joinpath('configs/' + args.language.lower() + "-template.yaml")
            if config_file.exists() is True:
                target_file = pathlib.Path(os.getcwd()).joinpath(args.language.lower() + "-template.yaml")

                if target_file.exists() is True:
                    print('❌ file already exists: ' + str(target_file))
                    return
                try:
                    shutil.copyfile(config_file, target_file)
                    print('✅ created config file from template: ' + str(target_file))
                except OSError as error:
                    LOGGER.error(f'{error}')
            else:
                print('❌ could not find the config template: ' + str(config_file))
            return

        if not args.yamlconfig:
            self.arg_parser.print_help()
            LOGGER.error('no yaml config given')
            return

        if args.verbose:
            LOGGER.set_logging_level_to_info()
            LOGGER.override_level_from_command_line_arg = True
        if args.debug:
            LOGGER.set_logging_level_to_debug()
            LOGGER.override_level_from_command_line_arg = True
        if args.error:
            LOGGER.set_logging_level_to_error()
            LOGGER.override_level_from_command_line_arg = True

        self.yaml_config_path = args.yamlconfig

    def print_config_dict(self) -> None:
        LOGGER.debug(self._get_own__dict__())

    def has_valid_config_path(self) -> bool:
        if self.yaml_config_path:
            return True
        return False

    def load_config_from_yaml_file(self, yaml_file_name: str) -> None:
        self._yaml_loader.load_config_from_yaml_file(yaml_file_name)
        self._validate_config()
        if self.valid:
            self._update_attributes_from_yaml_config()

    def _invalid_yaml_config(self, yaml_config) -> None:
        error_string = f'invalid yaml config: {yaml_config}'
        self.valid = False
        LOGGER.error(error_string)

    def _valid_yaml_config(self, yaml_config) -> None:
        LOGGER.debug(f'yaml config seems to be valid: {yaml_config}')
        self.valid = True

    # https://gist.github.com/PatrikHlobil/9d045e43fe44df2d5fd8b570f9fd78cc
    def iterate_all(self, iterable, returned="key"):
        if isinstance(iterable, dict):
            for key, value in iterable.items():
                if returned == "key":
                    yield key
                elif returned == "value":
                    if not (isinstance(value, dict) or isinstance(value, list)):
                        yield value
                else:
                    raise ValueError("'returned' keyword only accepts 'key' or 'value'.")
                for ret in self.iterate_all(value, returned=returned):
                    yield ret
        elif isinstance(iterable, list):
            for element in iterable:
                for ret in self.iterate_all(element, returned=returned):
                    yield ret

    @staticmethod
    def all_constant_names_from_config_enums() -> List[str]:
        all_constant_names = []
        for constant in ConfigKeyProject:
            if constant.name not in all_constant_names:
                all_constant_names.append(constant.name)

        for constant in ConfigKeyAnalysis:
            if constant.name not in all_constant_names:
                all_constant_names.append(constant.name)

        for constant in ConfigKeyEntityScan:
            if constant.name not in all_constant_names:
                all_constant_names.append(constant.name)

        for constant in ConfigKeyFileScan:
            if constant.name not in all_constant_names:
                all_constant_names.append(constant.name)

        for constant in ConfigKeyExport:
            if constant.name not in all_constant_names:
                all_constant_names.append(constant.name)

        return all_constant_names

    def _check_if_yaml_config_is_valid(self, yaml_config: Dict) -> bool:
        """Performs validity checks against a given yaml config.

        Args:
            yaml_config (Dict): A given yaml config.

        Returns:
            bool: True if the config is valid, otherwise False.
        """
        LOGGER.debug('running validity checks agains given config...')

        if not yaml_config:
            self._invalid_yaml_config(yaml_config)
            return False

        # config must have a project name
        if ConfigKeyProject.PROJECT_NAME.name.lower() not in yaml_config:
            self._invalid_yaml_config(yaml_config)
            return False

        # only valid keys within the projec level config?
        for key in yaml_config:
            if not ConfigKeyProject.valid(key):
                self._invalid_yaml_config(yaml_config)
                return False

        # config must have an analysis array ...
        if ConfigKeyProject.ANALYSES.name.lower() not in yaml_config:
            self._invalid_yaml_config(yaml_config)
            return False

        # ... which must be a list ...
        if not isinstance(yaml_config[ConfigKeyProject.ANALYSES.name.lower()], list):
            self._invalid_yaml_config(yaml_config)
            return False

        # ... which is not empty, and any entry in that list must have at least the following keys:
        # 'analysis_name', 'source_directory' and they have string values,
        # further there is at least one of 'file_scan' or 'entity_scan' per analysis
        analyses = yaml_config[ConfigKeyProject.ANALYSES.name.lower()]
        if not analyses or \
                not all(ConfigKeyAnalysis.ANALYSIS_NAME.name.lower() in analysis for analysis in analyses) or \
                not all(ConfigKeyAnalysis.SOURCE_DIRECTORY.name.lower() in analysis for analysis in analyses) or \
                not all(isinstance(analysis[ConfigKeyAnalysis.ANALYSIS_NAME.name.lower()], str) for analysis in analyses) or \
                not all(isinstance(analysis[ConfigKeyAnalysis.SOURCE_DIRECTORY.name.lower()], str) for analysis in analyses) or \
                not all(ConfigKeyAnalysis.FILE_SCAN.name.lower() in analysis or ConfigKeyAnalysis.ENTITY_SCAN.name.lower() in analysis for analysis in analyses):
            self._invalid_yaml_config(yaml_config)
            return False

        self._valid_yaml_config(yaml_config)
        return True

    def print_config_as_yaml(self):
        self._yaml_loader.print_yaml_config()

    def get_config_as_dict(self) -> Dict:
        return self._yaml_loader.get_config_as_dict()

    def contains_file_scan(self, analysis: Analysis) -> bool:
        """Checks if a given analysis was configured to do a file scan (to generate file results).

        Args:
            analysis (Analysis): A given analysis.

        Returns:
            bool: True if it was configured to do a file scan, otherwise False.
        """
        if ConfigKeyAnalysis.FILE_SCAN.name.lower() in analysis.scan_types:
            return True
        return False

    def contains_entity_scan(self, analysis: Analysis) -> bool:
        """Checks if a given analysis was configured to do an entity scan (to generate entity results).

        Args:
            analysis (Analysis): A given analysis.

        Returns:
            bool: True if it was configured to do an entity scan, otherwise False.
        """
        if ConfigKeyAnalysis.ENTITY_SCAN.name.lower() in analysis.scan_types:
            return True
        return False

    def _validate_config(self):
        yaml_config = self.get_config_as_dict()
        self._check_if_yaml_config_is_valid(yaml_config)

    # pylint: disable=too-many-nested-blocks,too-many-statements
    def _update_attributes_from_yaml_config(self):
        """Reads the yaml config, perfoms validity checks and initializes the current configuration."""
        LOGGER.debug(f'updating config attributes from yaml config...')
        yaml_config = self.get_config_as_dict()

        self.project_name = yaml_config[ConfigKeyProject.PROJECT_NAME.name.lower()]
        yaml_analyses = yaml_config[ConfigKeyProject.ANALYSES.name.lower()]

        # if the log level was not overridden from an command line argument
        if not LOGGER.override_level_from_command_line_arg:
            # check if there's any configured loglevel for the project and i
            if ConfigKeyProject.LOGLEVEL.name.lower() in yaml_config:
                if ConfigValProject.DEBUG.name.lower() in yaml_config[ConfigKeyProject.LOGLEVEL.name.lower()]:
                    LOGGER.set_logging_level_to_debug()
                if ConfigValProject.ERROR.name.lower() in yaml_config[ConfigKeyProject.LOGLEVEL.name.lower()]:
                    LOGGER.set_logging_level_to_error()
                if ConfigValProject.INFO.name.lower() in yaml_config[ConfigKeyProject.LOGLEVEL.name.lower()]:
                    LOGGER.set_logging_level_to_info()

        for analysis_dict in yaml_analyses:
            analysis: Analysis = Analysis()

            # check export config
            if ConfigKeyAnalysis.EXPORT.name.lower() in analysis_dict:
                for export_config in analysis_dict[ConfigKeyAnalysis.EXPORT.name.lower()]:
                    if ConfigKeyExport.DIRECTORY.name.lower() in export_config:
                        export_directory = export_config[ConfigKeyExport.DIRECTORY.name.lower()]
                        analysis.export_directory = export_directory
                    if ConfigKeyExport.GRAPHML.name.lower() in export_config:
                        analysis.export_graphml = True
                    if ConfigKeyExport.DOT.name.lower() in export_config:
                        analysis.export_dot = True
                    if ConfigKeyExport.TABULAR_FILE.name.lower() in export_config:
                        analysis.export_tabular_file = True
                    if ConfigKeyExport.TABULAR_CONSOLE_OVERALL.name.lower() in export_config:
                        analysis.export_tabular_console_overall = True
                    if ConfigKeyExport.TABULAR_CONSOLE.name.lower() in export_config:
                        analysis.export_tabular_console = True
                    if ConfigKeyExport.JSON.name.lower() in export_config:
                        analysis.export_json = True
                    if ConfigKeyExport.D3.name.lower() in export_config:
                        analysis.export_d3 = True

            # exclude directories and files from scanning
            if ConfigKeyAnalysis.IGNORE_DIRECTORIES_CONTAINING.name.lower() in analysis_dict:
                for directory in analysis_dict[ConfigKeyAnalysis.IGNORE_DIRECTORIES_CONTAINING.name.lower()]:
                    analysis.ignore_directories_containing.append(directory)

            # ignore files if given in the configuration
            if ConfigKeyAnalysis.IGNORE_FILES_CONTAINING.name.lower() in analysis_dict:
                for file in analysis_dict[ConfigKeyAnalysis.IGNORE_FILES_CONTAINING.name.lower()]:
                    analysis.ignore_files_containing.append(file)

            # ignore dependencies if given in the configuration
            if ConfigKeyAnalysis.IGNORE_DEPENDENCIES_CONTAINING.name.lower() in analysis_dict:
                for ignored_dependency in analysis_dict[ConfigKeyAnalysis.IGNORE_DEPENDENCIES_CONTAINING.name.lower()]:
                    analysis.ignore_dependencies_containing.append(ignored_dependency)

            # add replace dependency substring mappings
            if ConfigKeyAnalysis.IMPORT_ALIASES.name.lower() in analysis_dict:
                for mapping in analysis_dict[ConfigKeyAnalysis.IMPORT_ALIASES.name.lower()]:
                    for dependency_substring, replaced_dependency_substring in mapping.items():
                        if analysis.import_aliases_available == False:
                            analysis.import_aliases_available = True
                        analysis.import_aliases[dependency_substring] = replaced_dependency_substring

            # load metrics from analysis
            if ConfigKeyAnalysis.FILE_SCAN.name.lower() in analysis_dict:
                # add all configured file_scan metrics
                for configured_metric in analysis_dict[ConfigKeyAnalysis.FILE_SCAN.name.lower()]:

                    # necessary indicator what graph representations are relevant for graph based metrics
                    if configured_metric == ConfigKeyFileScan.DEPENDENCY_GRAPH.name.lower():
                        analysis.create_graph_representation(GraphType.FILE_RESULT_DEPENDENCY_GRAPH)

                    # number of methods
                    if configured_metric == ConfigKeyFileScan.NUMBER_OF_METHODS.name.lower():
                        number_of_methods_metric = NumberOfMethodsMetric(analysis)
                        LOGGER.debug(f'adding {number_of_methods_metric.pretty_metric_name}...')
                        analysis.metrics_for_file_results.update({
                            number_of_methods_metric.metric_name: number_of_methods_metric
                        })

                    # source lines of code
                    if configured_metric == ConfigKeyFileScan.SOURCE_LINES_OF_CODE.name.lower():
                        source_lines_of_code_metric = SourceLinesOfCodeMetric(analysis)
                        LOGGER.debug(f'adding {source_lines_of_code_metric.pretty_metric_name}...')
                        analysis.metrics_for_file_results.update({
                            source_lines_of_code_metric.metric_name: source_lines_of_code_metric
                        })

                    # fan-in, fan-out
                    if ConfigKeyFileScan.FAN_IN_OUT.name.lower() in configured_metric:
                        LOGGER.debug(f'adding {FanInOutMetric.pretty_metric_name}...')
                        graph_representations = analysis.existing_graph_representations
                        fan_in_out_metric = FanInOutMetric(analysis, graph_representations)
                        analysis.metrics_for_file_results.update({
                            fan_in_out_metric.metric_name: fan_in_out_metric
                        })

                    # louvain-modularity
                    if ConfigKeyFileScan.LOUVAIN_MODULARITY.name.lower() in configured_metric:
                        LOGGER.debug(f'adding {LouvainModularityMetric.pretty_metric_name}...')
                        graph_representations = analysis.existing_graph_representations
                        louvain_modularity_metric = LouvainModularityMetric(analysis, graph_representations)
                        analysis.metrics_for_file_results.update({
                            louvain_modularity_metric.metric_name: louvain_modularity_metric
                        })

                    # tfidf
                    if ConfigKeyFileScan.TFIDF.name.lower() in configured_metric:
                        LOGGER.debug(f'adding {TFIDFMetric.pretty_metric_name}...')
                        graph_representations = analysis.existing_graph_representations
                        tfidf_metric = TFIDFMetric(analysis)
                        analysis.metrics_for_file_results.update({
                            tfidf_metric.metric_name: tfidf_metric
                        })

                    # TODO: add more metrics

            if ConfigKeyAnalysis.ENTITY_SCAN.name.lower() in analysis_dict:
                for configured_metric in analysis_dict[ConfigKeyAnalysis.ENTITY_SCAN.name.lower()]:

                    # necessary indicator what graph representations are relevant for graph based metrics
                    if configured_metric == ConfigKeyEntityScan.DEPENDENCY_GRAPH.name.lower():
                        analysis.create_graph_representation(GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH)

                    if configured_metric == ConfigKeyEntityScan.INHERITANCE_GRAPH.name.lower():
                        analysis.create_graph_representation(GraphType.ENTITY_RESULT_INHERITANCE_GRAPH)

                    # TODO: check if dependency/inheritance exist
                    if configured_metric == ConfigKeyEntityScan.COMPLETE_GRAPH.name.lower():
                        analysis.create_graph_representation(GraphType.ENTITY_RESULT_COMPLETE_GRAPH)

                    # number of methods
                    if configured_metric == ConfigKeyEntityScan.NUMBER_OF_METHODS.name.lower():
                        LOGGER.debug(f'adding {NumberOfMethodsMetric.pretty_metric_name}...')
                        number_of_methods_metric = NumberOfMethodsMetric(analysis)

                        analysis.metrics_for_entity_results.update({
                            number_of_methods_metric.metric_name: number_of_methods_metric
                        })

                    # source lines of code
                    if configured_metric == ConfigKeyEntityScan.SOURCE_LINES_OF_CODE.name.lower():
                        LOGGER.debug(f'adding {SourceLinesOfCodeMetric.pretty_metric_name}...')
                        source_lines_of_code_metric = SourceLinesOfCodeMetric(analysis)
                        analysis.metrics_for_entity_results.update({
                            source_lines_of_code_metric.metric_name: source_lines_of_code_metric
                        })

                    # fan-in, fan-out
                    if ConfigKeyEntityScan.FAN_IN_OUT.name.lower() in configured_metric:
                        LOGGER.debug(f'adding {FanInOutMetric.pretty_metric_name}...')
                        graph_representations = analysis.existing_graph_representations
                        fan_in_out_metric = FanInOutMetric(analysis, graph_representations)

                        analysis.metrics_for_entity_results.update({
                            fan_in_out_metric.metric_name: fan_in_out_metric
                        })

                    # louvain-modularity
                    if ConfigKeyEntityScan.LOUVAIN_MODULARITY.name.lower() in configured_metric:
                        LOGGER.debug(f'adding {LouvainModularityMetric.pretty_metric_name}...')
                        graph_representations = analysis.existing_graph_representations
                        louvain_modularity_metric = LouvainModularityMetric(analysis, graph_representations)

                        analysis.metrics_for_entity_results.update({
                            louvain_modularity_metric.metric_name: louvain_modularity_metric
                        })

                     # tfidf
                    if ConfigKeyEntityScan.TFIDF.name.lower() in configured_metric:
                        LOGGER.debug(f'adding {TFIDFMetric.pretty_metric_name}...')
                        graph_representations = analysis.existing_graph_representations
                        tfidf_metric = TFIDFMetric(analysis)
                        analysis.metrics_for_entity_results.update({
                            tfidf_metric.metric_name: tfidf_metric
                        })

                    # TODO: add more metrics

            if ConfigKeyAnalysis.FILE_SCAN.name.lower() in analysis_dict:
                analysis.scan_types.append(ConfigKeyAnalysis.FILE_SCAN.name.lower())

            if ConfigKeyAnalysis.ENTITY_SCAN.name.lower() in analysis_dict:
                analysis.scan_types.append(ConfigKeyAnalysis.ENTITY_SCAN.name.lower())

            analysis.analysis_name = analysis_dict[ConfigKeyAnalysis.ANALYSIS_NAME.name.lower()]
            analysis.source_directory = analysis_dict[ConfigKeyAnalysis.SOURCE_DIRECTORY.name.lower()]

            # TODO: check for other optional keys/values and assign

            if ConfigKeyAnalysis.ONLY_PERMIT_LANGUAGES.name.lower() in analysis_dict:
                analysis.only_permit_languages = analysis_dict[ConfigKeyAnalysis.ONLY_PERMIT_LANGUAGES.name.lower()]
            if ConfigKeyAnalysis.ONLY_PERMIT_FILE_EXTENSIONS.name.lower() in analysis_dict:
                analysis.only_permit_file_extensions = analysis_dict[ConfigKeyAnalysis.ONLY_PERMIT_FILE_EXTENSIONS.name.lower()]

            self.analyses.append(analysis)


class YamlLoader:
    def __init__(self):
        self._file_name: str = ""
        self._config_file_content: str = ""
        self._schema_file_content: str = ""
        self._yaml: Dict = {}
        self._schema: Dict = {}

    def load_config_from_yaml_file(self, yaml_file_name: str) -> None:
        LOGGER.debug(f'trying to load yaml config...')
        self._load_config_file_content(yaml_file_name)
        self._load_yaml_from_config_file_content()

    def load_schema_from_yaml_file(self, yaml_file_name: str) -> None:
        LOGGER.debug(f'trying to load yaml schema...')
        self._load_config_file_content(yaml_file_name)
        self._load_yaml_from_config_file_content()

    def _validate_config_against_schema(self) -> bool:
        pass
        # config_dict = self.get_config_as_dict()
        # schema_dict = self.get_schema_as_dict()
        # now validate schema with cerberus

    def _load_schema_file_content(self, yaml_file_name) -> None:
        with open(yaml_file_name) as yaml_file:
            self._schema_file_content = yaml_file.read()

    def _load_config_file_content(self, yaml_file_name) -> None:
        try:
            with open(yaml_file_name) as yaml_file:
                self._config_file_content = yaml_file.read()
        except OSError:
            LOGGER.error(f'coould not open file: {yaml_file_name}')

    def _load_yaml_from_config_file_content(self):
        try:
            self._yaml = yaml.load(self._config_file_content, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            LOGGER.error(exc)

    def _load_yaml_from_schema_file_content(self):
        try:
            self._schema = yaml.load(self._schema_file_content, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            LOGGER.error(exc)

    def print_yaml_config(self):
        LOGGER.debug(yaml.dump(self._yaml))

    def get_config_as_dict(self) -> Dict:
        return self._yaml

    def get_schema_as_dict(self) -> Dict:
        return self._schema
