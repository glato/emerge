"""
Defines 'Analyzer' which brings together the current configuration, analyses, parsers and results.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import os
import logging
import coloredlogs
from datetime import datetime
from typing import List
# from emerge.fsm import EmergeFSM
from emerge.config import Configuration
from emerge.analysis import Analysis
from emerge.statistics import Statistics
from emerge.files import FileScanMapper, LanguageExtension, truncate_directory
from emerge.metrics.abstractmetric import AbstractCodeMetric, AbstractGraphMetric, AbstractMetric
from emerge.languages.abstractparser import AbstractParser
from emerge.logging import Logger

LOGGER = Logger(logging.getLogger('analysis'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class Analyzer:
    def __init__(self, config: Configuration, parsers):
        self._config: Configuration = config
        self._parsers = parsers
        self._results = {}

    def start_analyzing(self):
        """Starts every analysis found in the current configuration.
        """
        analyses_names = [x.analysis_name for x in self._config.analyses]
        LOGGER.info_start(f'starting to analyze {self._config.project_name}')
        LOGGER.debug(f'found the following analyses: ' + ', '.join(analyses_names))

        analysis: Analysis
        for i, analysis in enumerate(self._config.analyses, start=1):
            LOGGER.info(f'performing analysis {i}/{len(analyses_names)}: {analysis.analysis_name}')

            analysis.start_timer()
            self.start_scanning(analysis)
            analysis.stop_timer()
            analysis.statistics.add(key=Statistics.Key.ANALYSIS_RUNTIME, value=analysis.duration())
            self._clear_all_parsers()

    def start_scanning(self, analysis: Analysis):
        """Starts the scanning phase of a given analysis, depending on the current configuration:
        - Creates file/entity results 
        - Creates graph representations
        - Calculates metric results
        - Add local results to graph representations
        - Trigger exports for the collected results

        Args:
            analysis (Analysis): A given analysis.
        """

        # check if source directoy really exists, otherwise log error and throw exception
        if not os.path.isdir(analysis.source_directory):
            LOGGER.error(f'error in analysis {analysis.analysis_name}: source directory not found/ accessible: {analysis.source_directory}')
            raise NotADirectoryError(f'error in analysis {analysis.analysis_name}: source directory not found/ accessible: {analysis.source_directory}')

        if self._config.contains_file_scan(analysis) and not self._config.contains_entity_scan(analysis):
            self._create_file_results(analysis)

        if self._config.contains_entity_scan(analysis):
            self._create_file_results(analysis)
            self._create_entity_results(analysis)
        LOGGER.info_done('scanning complete')

        if analysis.contains_code_metrics:
            self._calculate_code_metric_results(analysis)

        if analysis.contains_graph_metrics:
            analysis.calculate_graph_representations()
            self._calculate_graph_metric_results(analysis)
            analysis.add_local_metric_results_to_graphs()
            analysis.export()

        self._collect_all_results()
        LOGGER.info_done('calculated and collected metric data')

    def _create_file_results(self, analysis: Analysis):
        """Checks configuration fow allowed directories/files/extensions,
        creates file results in a given analysis by perfoming a recursive file-scan.
        Adds statistics after the scan is finished.

        Args:
            analysis (Analysis): A given analysis.
        """
        LOGGER.info_start(f'starting token extraction for file results in {analysis.analysis_name}')
        LOGGER.info(f'starting scan at directory: {truncate_directory(analysis.source_directory)}')

        scanned_files, skipped_files = 0, 0
        scanning_starts = datetime.now()

        for root, dirs, files in os.walk(analysis.source_directory):
            # exclude directories and scans
            if analysis.ignore_directories_containing:
                dirs[:] = [d for d in dirs if d not in analysis.ignore_directories_containing]

            if analysis.ignore_files_containing:
                files[:] = [f for f in files if f not in analysis.ignore_files_containing]

            for file_name in files:
                absolute_path_to_file = os.path.join(root, file_name)
                file_name, file_extension = os.path.splitext(absolute_path_to_file)

                if not analysis.file_extension_allowed(file_extension):
                    if not file_extension.strip():
                        LOGGER.info(f'ignoring {absolute_path_to_file}')
                    else:
                        LOGGER.info(f'{file_extension} is not allowed in the scan, ignoring {absolute_path_to_file}')
                    skipped_files += 1
                    continue

                if not LanguageExtension.value_exists(file_extension):
                    LOGGER.info(f'{file_extension} is an unknown extension, ignoring {absolute_path_to_file}')
                    skipped_files += 1
                    continue

                file_name_with_extension = file_name + file_extension
                parser_name = FileScanMapper.choose_parser(file_extension, analysis.only_permit_languages)

                if parser_name in self._parsers:
                    parser: AbstractParser = self._parsers[parser_name]
                    file_content = parser.read_input_from_file(absolute_path_to_file)
                    parser.generate_file_result_from_analysis(analysis, file_name=file_name_with_extension, file_content=file_content)
                    scanned_files += 1
                    results = self._parsers[parser_name].results
                    analysis.add_results(results)

        for parser_name, parser in self._parsers.items():
            if bool(parser.results):
                parser.after_generated_file_results(analysis)

        scanning_stops = datetime.now()

        analysis.statistics.add(key=Statistics.Key.SCANNING_RUNTIME, value=scanning_stops - scanning_starts)
        analysis.statistics.add(key=Statistics.Key.SCANNED_FILES, value=scanned_files)
        analysis.statistics.add(key=Statistics.Key.SKIPPED_FILES, value=skipped_files)
        analysis.statistics.add(key=Statistics.Key.EXTRACTED_FILE_RESULTS, value=analysis.number_of_file_results)

    def _create_entity_results(self, analysis: Analysis):
        """Creates entity results from the file results of a given analysis for every active parser.
        After the results are stored in the analysis, statistics are added.

        Args:
            analysis (Analysis): A given analysis.
        """
        LOGGER.info_start(f'starting entity extraction in {analysis.analysis_name}')
        parser: AbstractParser
        for _, parser in self._parsers.items():
            if bool(parser.results):
                parser.generate_entity_results_from_analysis(analysis)
                analysis.results.update(parser.results)

        analysis.statistics.add(key=Statistics.Key.EXTRACTED_ENTITY_RESULTS, value=analysis.number_of_entity_results)

    @staticmethod
    def _calculate_code_metric_results(analysis: Analysis):
        """Calculates code metric results for a given analysis.

        Args:
            analysis (Analysis): A given analysis.
        """
        LOGGER.info_start(f'starting code metric calculation for analysis {analysis.analysis_name}')

        code_file_metrics = {k: v for (k, v) in analysis.metrics_for_file_results.items() if isinstance(v, AbstractCodeMetric)}
        code_entity_metrics = {k: v for (k, v) in analysis.metrics_for_entity_results.items() if isinstance(v, AbstractCodeMetric)}
        ordered_metric_calculations: List = [code_file_metrics, code_entity_metrics]

        for metric_mapping in ordered_metric_calculations:
            if bool(metric_mapping):
                metric: AbstractMetric
                for _, metric in metric_mapping.items():
                    analysis.calculate_metric(metric)

        LOGGER.info_done('done calculating code metric results')

    @staticmethod
    def _calculate_graph_metric_results(analysis: Analysis):
        """Calculates graph metric results for a given analysis.

        Args:
            analysis (Analysis): A given analysis.
        """
        LOGGER.info_start(f'starting graph metric calculation for analysis {analysis.analysis_name}')

        graph_file_metrics = {k: v for (k, v) in analysis.metrics_for_file_results.items() if isinstance(v, AbstractGraphMetric)}
        graph_entity_metrics = {k: v for (k, v) in analysis.metrics_for_entity_results.items() if isinstance(v, AbstractGraphMetric)}
        ordered_metric_calculations: List = [graph_file_metrics, graph_entity_metrics]

        for metric_mapping in ordered_metric_calculations:
            if bool(metric_mapping):
                metric: AbstractMetric
                for _, metric in metric_mapping.items():
                    analysis.calculate_metric(metric)

        LOGGER.info_done('done calculating graph metric results')

    def _collect_all_results(self):
        """Collects results from all configured analyses.
        """
        for analysis in self._config.analyses:
            LOGGER.debug(f'collecting results from analysis: {analysis.analysis_name}')
            self._results.update(analysis.results)

    def _clear_all_parsers(self):
        """Clears all results from available parsers.
        """
        parser: AbstractParser
        for _, parser in self._parsers.items():
            parser.results.clear()
            pass
