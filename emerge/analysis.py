"""
An Analysis holds configuration, metrics and the generated results.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import List, Dict, Any, Optional, Set
import logging
from datetime import datetime, timedelta
import os
from pathlib import Path
import coloredlogs

from emerge.languages.abstractparser import AbstractResult, AbstractParser, LanguageType
from emerge.metrics.abstractmetric import AbstractMetric, AbstractCodeMetric, AbstractGraphMetric, MetricResultFilter

from emerge.files import FileManager
from emerge.abstractresult import AbstractEntityResult, AbstractFileResult
from emerge.graph import GraphRepresentation, GraphType, FileSystemNode, FileSystemNodeType
from emerge.stats import Statistics
from emerge.log import Logger
from emerge.core import format_timedelta
from emerge.files import truncate_directory, LanguageExtension

from emerge.export import GraphExporter, TableExporter, JSONExporter, DOTExporter, D3Exporter


LOGGER = Logger(logging.getLogger('analysis'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class Analysis:
    """Contains the configuration for a concrete source analysis, responsible for calculating code/graph metrics and results."""

    def __init__(self):
        self.scan_types: List[str] = []

        self.metrics_for_file_results: Dict[str, AbstractMetric] = {}
        self.metrics_for_entity_results: Dict[str, AbstractMetric] = {}

        self.analysis_name: Optional[str] = None
        self.project_name: Optional[str] = None
        self.source_directory: Optional[str] = None

        self.export_directory: Optional[str] = None
        self.export_graphml: bool = False
        self.export_tabular_file: bool = False
        self.export_tabular_console_overall: bool = False
        self.export_tabular_console: bool = False
        self.analysis_date: Optional[str] = None
        self.analysis_runtime: Optional[str] = None

        # additional config / node radius multiplication by metric
        self.radius_fan_in: Optional[float] = 0.1
        self.radius_fan_out: Optional[float] = 0.1
        self.radius_louvain: Optional[float] = 0.02
        self.radius_sloc: Optional[float] = 0.005
        self.radius_number_of_methods: Optional[float] = 0.05

        # additional config / heatmap
        self.heatmap_sloc_active: Optional[bool] = True
        self.heatmap_fan_out_active: Optional[bool] = True
        self.heatmap_sloc_weight: Optional[float] = 1.5
        self.heatmap_fan_out_weight: Optional[float] = 1.7
        self.heatmap_score_base: Optional[int] = 10
        self.heatmap_score_limit: Optional[int] = 300

        self.emerge_version: Optional[str] = None

        self.export_json: bool = False
        self.export_dot: bool = False
        self.export_d3: bool = False

        self.only_permit_languages: List[LanguageType] = []
        self.only_permit_file_extensions: List[str] = []
        self.only_permit_files_matching_absolute_path_available: bool = False
        self.only_permit_files_matching_absolute_path: List[str] = []
        self.ignore_directories_containing: List = []
        self.ignore_files_containing: List = []
        self.ignore_dependencies_containing: List[str] = []
        self.ignore_entities_containing: List[str] = []
        self.import_aliases_available: bool = False
        self.import_aliases: Dict[str, str] = {}

        self.results: Dict[str, AbstractResult] = {}

        self.absolute_scanned_file_names: Set[str] = set()

        # memoization
        self.scanned_files_nodes_in_directories = {}

        self.local_metric_results: Dict[str, Dict[str, Any]] = {}
        self.overall_metric_results: Dict[str, Any] = {}

        self.graph_representations: Dict[str, GraphRepresentation] = {
            GraphType.ENTITY_RESULT_COMPLETE_GRAPH.name.lower(): None,
            GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH.name.lower(): None,
            GraphType.ENTITY_RESULT_INHERITANCE_GRAPH.name.lower(): None,
            GraphType.FILE_RESULT_DEPENDENCY_GRAPH.name.lower(): None,
            GraphType.FILESYSTEM_GRAPH.name.lower(): None
        }

        self._start_time: datetime = None
        self._stop_time: datetime = None
        self.total_runtime: Optional[str] = None

        self.statistics = Statistics()

    def add_results(self, results) -> None:
        """Add results to this analysis.

        Args:
            results (Any subclass of AbstractResult): the results.
        """
        self.results.update(results)

    def collect_results_from_parser(self, parser: AbstractParser) -> None:
        """Collect results from a given parser.

        Args:
            parser (AbstractParser): instance of the given parser.
        """
        if bool(parser.results):
            self.results.update(parser.results)

    def collect_local_metric_results(self, results: Dict[str, Any]) -> None:
        """Collect local metric results, e.g. results that are bound to a specific file or entity result.

        Args:
            results (Dict[str, Any]): A dictionary given by result name / subclass of AbstractResult.
        """
        for name, metric_dict in results.items():
            if name in self.local_metric_results:
                self.local_metric_results[name].update(metric_dict)
            else:
                self.local_metric_results[name] = metric_dict

    def collect_overall_metric_results(self, results: Dict[str, Any]) -> None:
        """Collect overall metric results, e.g. results that were calculated from a set of file or entity results.

        Args:
            results (Dict[str, Any]): A dictionary given by result name / subclass of AbstractResult.
        """
        self.overall_metric_results.update(results)

    def duration(self) -> Optional[timedelta]:
        """Returns an optinal duration of the whole analysis.

        Returns:
            Optional[datetime]: Returns the duration of the anaylsis, if it was measured by start and stop time.
        """
        if self._start_time and self._stop_time:
            return self._stop_time - self._start_time
        else:
            return None

    def contains_metric_for_file_results(self, metric_name: str) -> bool:
        """Checks if the analysis contains a file result metric given by a metric name.

        Args:
            metric_name (str): a given metric name.

        Returns:
            bool: True if it contains the metric, False otherwise.
        """
        if metric_name.lower() in self.metrics_for_file_results:
            return True
        return False

    def contains_metric_for_entity_results(self, metric_name: str) -> bool:
        """Checks if the analysis contains an entity result metric given by a metric name.

        Args:
            metric_name (str): a given metric name.

        Returns:
            bool: True if it contains the metric, False otherwise.
        """
        if metric_name.lower() in self.metrics_for_entity_results:
            return True
        return False

    def contains_metrics(self) -> bool:
        """Checks if the analysis contains any metrics.

        Returns:
            bool: True if it contains any metrics, otherweise False.
        """
        if bool(self.metrics_for_entity_results) or bool(self.metrics_for_file_results):
            return True
        return False

    @property
    def contains_code_metrics(self) -> bool:
        """Checks if the analysis contains any code metrics (for file or entity results).

        Returns:
            bool: True if the analysis contains any code metrics, otherwise False.
        """
        code_file_metrics = {k: v for (k, v) in self.metrics_for_file_results.items() if isinstance(v, AbstractCodeMetric)}
        code_entity_metrics = {k: v for (k, v) in self.metrics_for_entity_results.items() if isinstance(v, AbstractCodeMetric)}
        if bool(code_file_metrics) or bool(code_entity_metrics):
            return True
        return False

    @property
    def contains_graph_metrics(self) -> bool:
        """Checks if the analysis contains any graph metrics (for file or entity results).

        Returns:
            bool: True if the analysis contains any graph metrics, otherwise False.
        """
        graph_file_metrics = {k: v for (k, v) in self.metrics_for_file_results.items() if isinstance(v, AbstractGraphMetric)}
        graph_entity_metrics = {k: v for (k, v) in self.metrics_for_entity_results.items() if isinstance(v, AbstractGraphMetric)}
        if bool(graph_file_metrics) or bool(graph_entity_metrics):
            return True
        return False

    def calculate_metric(self, metric: AbstractMetric) -> None:
        """Calculates a metric given by any subclass of AbstractMetric, collects local and overall metric results and add metric runtime to statistics.

        Args:
            metric (AbstractMetric): A metric can be any subclass of AbstractMetric.
        """

        start_metric_calculation = datetime.now()

        if self.contains_metric_for_entity_results(metric.metric_name):

            filtered_results = self.filtered_results(MetricResultFilter.ENTITY_RESULTS)
            metric.calculate_from_results(filtered_results)
            self.collect_local_metric_results(metric.local_data)
            self.collect_overall_metric_results(metric.overall_data)

        if self.contains_metric_for_file_results(metric.metric_name):

            filtered_results = self.filtered_results(MetricResultFilter.FILE_RESULTS)
            metric.calculate_from_results(filtered_results)
            self.collect_local_metric_results(metric.local_data)
            self.collect_overall_metric_results(metric.overall_data)

        stop_metric_calculcation = datetime.now()
        metric_runtime = stop_metric_calculcation - start_metric_calculation

        self.statistics.add(key=Statistics.Key.RUNTIME, value=metric_runtime, prefix=metric.metric_name)

    def export(self) -> None:
        """Triggers all exports that are configured within this analysis. Collects statistics, metric results and exports them to the configured outputs.
        """

        if self.export_directory is None:
            self.export_directory = os.getcwd()

        # check if export directoy really exists, otherwise log error and throw exception
        if not os.path.isdir(self.export_directory):
            LOGGER.error(f'export directory not found/ accessible: {self.export_directory}')
            raise NotADirectoryError(f'export directory not found/ accessible: {self.export_directory}')

        statistics: Dict[str, Any] = self.get_statistics()
        overall_metric_results: Dict[str, Any] = self.get_overall_metric_results()
        local_metric_results: Dict[str, Dict[str, Any]] = self.get_local_metric_results()

        analysis_name = "unnamed_anaylsis"
        if self.analysis_name:
            analysis_name = self.analysis_name

        if self.export_graphml:
            created_graph_representations = {k: v for (k, v) in self.graph_representations.items() if v is not None}
            representation: GraphRepresentation
            for _, representation in created_graph_representations.items():
                GraphExporter.export_graph_as_graphml(representation.digraph, representation.graph_type.name.lower(), self.export_directory)

        if self.export_dot:
            created_graph_representations = {k: v for (k, v) in self.graph_representations.items() if v is not None}
            for _, representation in created_graph_representations.items():
                DOTExporter.export_graph_as_dot(representation.digraph,
                                                representation.graph_type.name.lower(), self.export_directory)

        if self.export_d3:
            created_graph_representations = {k: v for (k, v) in self.graph_representations.items() if v is not None}
            FileManager.copy_force_graph_template_to_export_dir(self.export_directory)
            D3Exporter.export_d3_force_directed_graph(
                created_graph_representations, statistics, overall_metric_results, self, self.export_directory
            )

        if self.export_tabular_file:
            TableExporter.export_statistics_and_metrics_as_file(statistics, overall_metric_results, local_metric_results, analysis_name, self.export_directory)

        if self.export_json:
            JSONExporter.export_statistics_and_metrics(statistics, overall_metric_results, local_metric_results, analysis_name, self.export_directory)

        if self.export_tabular_console_overall:
            TableExporter.export_statistics_and_metrics_to_console(statistics, overall_metric_results, None, analysis_name)
        elif self.export_tabular_console:
            TableExporter.export_statistics_and_metrics_to_console(statistics, overall_metric_results, local_metric_results, analysis_name)

        resolved_export_path = Path(self.export_directory).resolve()

        LOGGER.info_done(f'all your generated/exported data can be found here: {resolved_export_path}')
        if self.export_d3:
            LOGGER.info_done(f'copy the following path to your browser and start your web app: 👉 file://{resolved_export_path}/html/emerge.html')

    @property
    def entity_results(self) -> Dict[str, AbstractEntityResult]:
        """Returns a dictionary of all entity results from this analysis.

        Returns:
            Dict[str, AbstractEntityResult]: entity results hashed by name.
        """
        entity_results: Dict[str, AbstractEntityResult] = {k: v for (k, v) in self.results.items() if isinstance(v, AbstractEntityResult)}
        return entity_results

    @property
    def file_results(self) -> Dict[str, AbstractFileResult]:
        """Returns a dictionary of all file results from this analysis.

        Returns:
            Dict[str, AbstractFileResult]: file results hashed by name.
        """
        file_results: Dict[str, AbstractFileResult] = {k: v for (k, v) in self.results.items() if isinstance(v, AbstractFileResult)}
        return file_results

    @property
    def number_of_file_results(self) -> int:
        """Returns the number of file results from this analysis.

        Returns:
            int: number of file results.
        """
        return len(self.file_results)

    @property
    def number_of_entity_results(self) -> int:
        """Returns the number of entity results from this analysis.

        Returns:
            int: number of entity results.
        """
        return len(self.entity_results)

    def filtered_results(self, result_filter: MetricResultFilter) -> Dict[str, Any]:
        """Returns a filtered set of metric results, based on MetricResultFilter.

        Args:
            result_filter (MetricResultFilter): set filter either for entity or file results.

        Returns:
            Dict[str, AbstractResult]: Return the filtered set of metric results.
        """
        if result_filter == MetricResultFilter.ENTITY_RESULTS:
            return self.entity_results
        if result_filter == MetricResultFilter.FILE_RESULTS:
            return self.file_results
        return {}

    def result_by_entity_name(self, name: str, results: Any) -> Optional[AbstractEntityResult]:
        """Returns the first found result given by entity name, otherwise None.

        Args:
            name (str): entity name of the result.

        Returns:
            Optional[AbstractEntityResult]: the first found result given by entity name, otherwise None.
        """
        res: Dict[str, AbstractEntityResult] = {k: v for (k, v) in results.items() if isinstance(v, AbstractEntityResult) and v.entity_name == name}
        if bool(res):
            return res[list(res.keys())[0]]
        return None

    def result_by_unique_name(self, unique_name: str) -> Optional[AbstractResult]:
        """Returns the first found result given by unique name, otherwise None.

        Args:
            unique_name (str): unique name of the result.

        Returns:
            Optional[AbstractResult]: the first found result given by unique name, otherwise None.
        """
        results: Dict[str, AbstractResult] = {k: v for (k, v) in self.results.items() if isinstance(v, AbstractResult) and v.unique_name == unique_name}
        if bool(results):
            return results[list(results.keys())[0]]
        return None

    def create_graph_representation(self, graph_type: GraphType) -> None:
        """Creates a graph representation in this analysis, given by a graph type.

        Args:
            graph_type (GraphType): The specific graph type.
        """
        if self.graph_representations[graph_type.name.lower()] is None:
            self.graph_representations[graph_type.name.lower()] = GraphRepresentation(graph_type)

    def create_filesystem_graph(self) -> None:
        """Creates a filesystem graph which is basically a graph representation of the project filesystem tree.
        This filesystem graph is used for further calculations and metric results.
        The filesystem graph does NOT contain file content, only the graph structure. The content is stored in the self.filesyste_nodes dict.
        """

        if self.source_directory is None:
            raise Exception('source_directory is not set')

        LOGGER.info_start(f'starting to create filesystem graph in {self.analysis_name}')
        LOGGER.info(f'starting scan at directory: {truncate_directory(self.source_directory)}')

        scanned_files, skipped_files = 0, 0
        scanning_starts = datetime.now()

        filesystem_graph = self.graph_representations[GraphType.FILESYSTEM_GRAPH.name.lower()]

        # create a root directory filesystem node, add to project graph

        parent_analysis_source_path = f"{Path(self.source_directory).parent}/"
        relative_file_path_to_analysis = self.source_directory.replace(parent_analysis_source_path, "")

        filesystem_root_node = FileSystemNode(FileSystemNodeType.DIRECTORY, relative_file_path_to_analysis)
        filesystem_graph.filesystem_nodes[filesystem_root_node.absolute_name] = filesystem_root_node

        filesystem_graph.digraph.add_node(
            filesystem_root_node.absolute_name,
            directory=True,
            file=False,
            display_name=filesystem_root_node.absolute_name
        )

        for root, dirs, files in os.walk(self.source_directory):
            # exclude directories and scans

            if self.ignore_directories_containing:
                dirs[:] = [d for d in dirs if d not in self.ignore_directories_containing]

            for directory in dirs:
                absolute_path_to_directory = os.path.join(root, directory)

                # create relative analysis paths to exactly match the same path of nodes in other graphs (and get their metrics)
                parent_analysis_source_path = f"{Path(absolute_path_to_directory).parent}/"
                relative_file_path_to_analysis = absolute_path_to_directory.replace(parent_analysis_source_path, "")
                relative_path_parent = f'{Path(root)}'.replace(f'{ Path(self.source_directory).parent}/', "")
                relative_path_directoy_node = f'{Path(root)}/{relative_file_path_to_analysis}'.replace(f"{Path(self.source_directory).parent}/", "")

                directory_node = FileSystemNode(FileSystemNodeType.DIRECTORY, relative_path_directoy_node)
                filesystem_graph.filesystem_nodes[directory_node.absolute_name] = directory_node

                filesystem_graph.digraph.add_node(
                    directory_node.absolute_name,
                    directory=True,
                    file=False,
                    display_name=directory_node.absolute_name
                )

                filesystem_graph.digraph.add_edge(relative_path_parent, relative_path_directoy_node)

            if self.ignore_files_containing:
                files[:] = [f for f in files if f not in self.ignore_files_containing]

            for file_name in files:
                absolute_path_to_file = os.path.join(root, file_name)

                # check if the scan should only allow specific files
                if self.only_permit_files_matching_absolute_path_available:
                    if absolute_path_to_file not in self.only_permit_files_matching_absolute_path:
                        skipped_files += 1
                        LOGGER.info(f'ignoring file {absolute_path_to_file} due to only_scan_files restriction')
                        continue
                    else:
                        LOGGER.info(f'got file {absolute_path_to_file}')

                # watch out for symlinks
                if os.path.islink(absolute_path_to_file):
                    LOGGER.debug(f'possible symlink found: {absolute_path_to_file}')
                    absolute_path_to_file_resolved_symlink = os.path.realpath(absolute_path_to_file)
                    if os.path.exists(absolute_path_to_file_resolved_symlink):
                        absolute_path_to_file = absolute_path_to_file_resolved_symlink
                        LOGGER.debug(f'could resolve symlink {absolute_path_to_file} to {absolute_path_to_file_resolved_symlink}')
                    else:
                        LOGGER.warning(f'ignoring unresolvable symlink {absolute_path_to_file}')
                        continue

                file_name, file_extension = os.path.splitext(absolute_path_to_file)

                # create relative analysis path to exactly match the same path of nodes in other graphs (and get their metrics)
                parent_analysis_source_path = f"{Path(absolute_path_to_file).parent}/"
                relative_root = f'{Path(root)}'.replace(f'{ Path(self.source_directory).parent}/', "")
                relative_file_path_to_analysis = absolute_path_to_file.replace(f'{Path(self.source_directory).parent}/', "")

                if not self.file_extension_allowed(file_extension):
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

                # build up a set of relative names to speed up computational checks later
                # also add it as property to the filesystem graph
                self.absolute_scanned_file_names.add(relative_file_path_to_analysis)

                if relative_root not in self.scanned_files_nodes_in_directories:
                    self.scanned_files_nodes_in_directories[relative_root] = []
                    self.scanned_files_nodes_in_directories[relative_root].append(relative_file_path_to_analysis)
                else:
                    self.scanned_files_nodes_in_directories[relative_root].append(relative_file_path_to_analysis)
                   
                with open(absolute_path_to_file, encoding="ISO-8859-1") as file:
                    file_content = file.read()
                    file_node = FileSystemNode(FileSystemNodeType.FILE, relative_file_path_to_analysis, file_content)
                    filesystem_graph.filesystem_nodes[file_node.absolute_name] = file_node

                    filesystem_graph.digraph.add_node(
                        file_node.absolute_name,
                        directory=False,
                        file=True,
                        display_name=Path(file_node.absolute_name).name,
                        result_name=relative_file_path_to_analysis
                    )

                    filesystem_graph.digraph.add_edge(relative_root, file_node.absolute_name)

                    scanned_files += 1

        scanning_stops = datetime.now()

        self.statistics.add(key=Statistics.Key.SCANNING_RUNTIME, value=scanning_stops - scanning_starts)
        self.statistics.add(key=Statistics.Key.SCANNED_FILES, value=scanned_files)
        self.statistics.add(key=Statistics.Key.SKIPPED_FILES, value=skipped_files)

    def calculate_graph_representations(self) -> None:
        """Calculate all necessary graph representations for this analysis in a specific order.
        """
        file_results = {k: v for (k, v) in self.results.items() if isinstance(v, AbstractFileResult)}
        entity_results = {k: v for (k, v) in self.results.items() if isinstance(v, AbstractEntityResult)}

        # make sure we compute dependency/inheritance graphs before composing complete graphs
        simple_graph_representations = {k: v for (k, v) in self.graph_representations.items() if v is not None and
                                        v.graph_type is not GraphType.ENTITY_RESULT_COMPLETE_GRAPH}

        complete_graph_representation = {k: v for (k, v) in self.graph_representations.items() if v is not None and
                                         v.graph_type is GraphType.ENTITY_RESULT_COMPLETE_GRAPH}

        representation: GraphRepresentation
        for name, representation in simple_graph_representations.items():

            if name == GraphType.FILE_RESULT_DEPENDENCY_GRAPH.name.lower():
                representation.calculate_dependency_graph_from_results(file_results)

            if name == GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH.name.lower():
                representation.calculate_dependency_graph_from_results(entity_results)

            if name == GraphType.ENTITY_RESULT_INHERITANCE_GRAPH.name.lower():
                representation.calculate_inheritance_graph_from_results(entity_results)

        # now if necessary compute the compositions
        for name, representation in complete_graph_representation.items():
            if name == GraphType.ENTITY_RESULT_COMPLETE_GRAPH.name.lower():
                if simple_graph_representations[GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH.name.lower()] is not None and \
                   simple_graph_representations[GraphType.ENTITY_RESULT_INHERITANCE_GRAPH.name.lower()] is not None:
                    representation.calculate_complete_graph(
                        dependency_graph_repr=simple_graph_representations[GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH.name.lower()],
                        inheritance_graph_repr=simple_graph_representations[GraphType.ENTITY_RESULT_INHERITANCE_GRAPH.name.lower()]
                    )

    def add_local_metric_results_to_graphs(self) -> None:
        """Adds local metric results to all existing graph representations within this analysis.
        """
        actual_graph_representation = self.existing_graph_representations
        for _, graph in actual_graph_representation.items():
            graph.add_local_metric_results_to_graph_nodes(self.local_metric_results)

    @ property
    def existing_graph_representations(self) -> Dict[str, GraphRepresentation]:
        """Returns the instantiated graph representations in the analysis.

        Returns:
            Dict[str, GraphRepresentation]: A dictionary of existing graph representations.
        """
        return {k: v for (k, v) in self.graph_representations.items() if v is not None}

    def start_timer(self) -> None:
        self._start_time = datetime.now()

    def stop_timer(self) -> None:
        self._stop_time = datetime.now()

    def print_all_results(self) -> None:
        for _, result in self.results.items():
            LOGGER.debug(f'{result=}')

    def print_statistics(self) -> None:
        """Prints collected statistics from the analysis.
        """
        LOGGER.info_start(f'the following statistics were collected in {self.analysis_name}')
        for name, value in self.statistics.data.items():
            if isinstance(value, timedelta):
                formatted_value = format_timedelta(value, '%H:%M:%S + %s ms')
                LOGGER.info(f'{name}: {formatted_value}')
            else:
                LOGGER.info(f'{name}: {value}')

    def get_statistics(self) -> Dict[str, Any]:
        """Returns collected statistics from the analysis.

        Returns:
            Dict[str, Any]: A dictionary of collected statistics from the analysis.
        """
        statistics = {}
        for name, value in self.statistics.data.items():
            if isinstance(value, timedelta):
                formatted_value = format_timedelta(value, '%H:%M:%S + %s ms')
                statistics[name] = formatted_value
            else:
                statistics[name] = value
        return statistics

    def print_overall_metric_results(self) -> None:
        LOGGER.info_start(f'the following metrics were collected in {self.analysis_name}')
        for name, value in self.overall_metric_results.items():
            if isinstance(value, float):
                LOGGER.info(f'{name}: {value:.2f}')
            else:
                LOGGER.info(f'{name}: {value}')

    def get_overall_metric_results(self) -> Dict[str, Any]:
        """Returns calculated overall metric results from the analysis.

        Returns:
            Dict[str, Any]: A dictionary of calculated overall metric results from the analysis.
        """
        metric_results = {}
        for name, value in self.overall_metric_results.items():
            metric_results[name] = value
        return metric_results

    def get_local_metric_results(self) -> Dict[str, Dict[str, Any]]:
        return self.local_metric_results

    def file_extension_allowed(self, file_extension: str) -> bool:
        """Checks if a given file extension can be considered for scanning source code in this analysis.

        Args:
            file_extension (str): the given file extension.

        Returns:
            bool: True, if configured in self.only_permit_file_extensions, otherwise False
        """
        if file_extension in self.only_permit_file_extensions:
            return True
        return False
