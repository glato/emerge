"""
Defines 'Analyzer' which brings together the current configuration, analyses, parsers and results.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import os
import logging
from typing import Any, List, Dict
from pathlib import Path

from datetime import datetime
import coloredlogs

from emerge.metrics.abstractmetric import AbstractCodeMetric, AbstractGraphMetric, AbstractMetric
from emerge.languages.abstractparser import AbstractParser

from emerge.graph import GraphType, FileSystemNode, FileSystemNodeType
from emerge.config import Configuration
from emerge.analysis import Analysis
from emerge.stats import Statistics
from emerge.files import FileScanMapper
from emerge.log import Logger
from emerge.core import format_timedelta

LOGGER = Logger(logging.getLogger('analysis'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class Analyzer:
    def __init__(self, config: Configuration, parsers):
        self._config: Configuration = config
        self._parsers = parsers
        self._results: Dict[str, Any] = {}

    def start_analyzing(self):
        """Starts every analysis found in the current configuration.
        """
        analyses_names = [x.analysis_name for x in self._config.analyses]
        LOGGER.info_start(f'starting to analyze {self._config.project_name}')
        LOGGER.debug('found the following analyses: ' + ', '.join(analyses_names))

        analysis: Analysis
        for i, analysis in enumerate(self._config.analyses, start=1):
            LOGGER.info(f'performing analysis {i}/{len(analyses_names)}: {analysis.analysis_name}')

            analysis.analysis_date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

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

        start_time = datetime.now()

        if analysis.source_directory is None:
            raise Exception('source directory is not set')

         # check if source directoy really exists, otherwise log error and throw exception
        if not os.path.isdir(analysis.source_directory):
            LOGGER.error(f'error in analysis {analysis.analysis_name}: source directory not found/ accessible: {analysis.source_directory}')
            raise NotADirectoryError(f'error in analysis {analysis.analysis_name}: source directory not found/ accessible: {analysis.source_directory}')

        self._create_filesystem_graph(analysis)
        LOGGER.info_done('created the filesystem graph')

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

        self._collect_all_results()

        stop_time = datetime.now()
        delta_total_runtime = stop_time - start_time
        analysis.total_runtime = format_timedelta(delta_total_runtime, '%H:%M:%S + %s ms')
        analysis.statistics.add(key=Statistics.Key.TOTAL_RUNTIME, value=analysis.total_runtime)
        analysis.export()

        LOGGER.info_done(f'total runtime of analysis: {analysis.total_runtime}')

    def _create_filesystem_graph(self, analysis: Analysis):
        """Creates a project graph as a basis for all further file-based calculations.
        """
        analysis.create_graph_representation(GraphType.FILESYSTEM_GRAPH)
        analysis.create_filesystem_graph()

    def _create_file_results(self, analysis: Analysis):
        """Iterate over all filesystem nodes from the given analysis, create FileResult objects and add it to the analysis.

        Args:
            analysis (Analysis): A given analysis.
        """

        LOGGER.info_start(f'starting file result creation in {analysis.analysis_name}')
        file_result_creation_starts = datetime.now()

        filesystem_graph = analysis.graph_representations[GraphType.FILESYSTEM_GRAPH.name.lower()]

        project_node: FileSystemNode
        for _, filesystem_node in filesystem_graph.filesystem_nodes.items():
            project_node = filesystem_node

            if project_node.type == FileSystemNodeType.FILE:
                file_extension = Path(project_node.absolute_name).suffix
                file_name = Path(project_node.absolute_name).name

                parser_name = FileScanMapper.choose_parser(file_extension, analysis.only_permit_languages)

                if parser_name in self._parsers:
                    parser: AbstractParser = self._parsers[parser_name]

                    file_content = project_node.content

                    if file_content is None:
                        raise Exception(f'file content is None for file: {project_node.absolute_name}')
                    
                    parser.generate_file_result_from_analysis(
                        analysis,
                        file_name=file_name,
                        full_file_path=project_node.absolute_name,
                        file_content=file_content
                    )
                    
                    results = self._parsers[parser_name].results
                    analysis.add_results(results)

        for parser_name, parser in self._parsers.items():
            if bool(parser.results):
                parser.after_generated_file_results(analysis)

        file_result_creation_stops = datetime.now()

        analysis.statistics.add(key=Statistics.Key.EXTRACTED_FILE_RESULTS, value=analysis.number_of_file_results)
        analysis.statistics.add(key=Statistics.Key.FILE_RESULTS_CREATION_RUNTIME, value=file_result_creation_stops - file_result_creation_starts)

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
                    LOGGER.info(f'calculating code metric results for: {metric.pretty_metric_name}')
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
                    LOGGER.info(f'calculating graph metric results for: {metric.pretty_metric_name}')
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
