"""
Contains all classes related to exporters, e.g. GraphExporter.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, Any, Optional
from collections import OrderedDict

# from logging import Logger
import json

import logging
import coloredlogs

import networkx as nx
from networkx.readwrite import json_graph
from networkx.drawing.nx_agraph import write_dot
from prettytable import PrettyTable

from emerge.graph import GraphRepresentation, GraphType
from emerge.log import Logger

LOGGER = Logger(logging.getLogger('analysis'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class GraphExporter:
    def __init__(self):
        ...

    @staticmethod
    def export_graph_as_graphml(graph, export_name, export_dir):
        nx.write_graphml(graph, export_dir + '/' + 'emerge-' + export_name + '.graphml')


class TableExporter:
    def __init__(self):
        ...

    @staticmethod
    def export_statistics_and_metrics_to_console(
            statistics: Dict[str, Any],
            overall_metric_results: Dict[str, Any],
            local_metric_results: Optional[Dict[str, Dict[str, Any]]],
            analysis_name: str
        ):
        """Prints all collected statistics, overall metric results and local metric results to console by using a prettytable."""

        # overall statistics
        if bool(statistics):
            LOGGER.info_start(f'the following statistics were collected in {analysis_name}')
            tab_statistics = PrettyTable(['statistic name', 'value'])
            tab_statistics.align['statistic name'] = "r"
            tab_statistics.align['value'] = "l"

            for name, value in statistics.items():
                tab_statistics.add_row([name, value])
            print(tab_statistics)

        # overall metrics
        if bool(overall_metric_results):
            LOGGER.info_start(f'the following overall metrics were collected in {analysis_name}')
            tab_metric_results = PrettyTable(['metric name', 'value'])
            tab_metric_results.align['metric name'] = "r"
            tab_metric_results.align['value'] = "l"

            for name, value in overall_metric_results.items():
                if isinstance(value, dict):
                    values_as_string = ', '.join(str(x) for x in value.values())
                    tab_metric_results.add_row([name, values_as_string])
                elif isinstance(value, str):
                    tab_metric_results.add_row([name, value])
                else:
                    tab_metric_results.add_row([name, round(value, 2)])
            print(tab_metric_results)

        # local metrics
        if local_metric_results is not None and bool(local_metric_results):
            LOGGER.info_start(f'the following local metrics were collected in {analysis_name}')

            left_width, right_width = 0, 0
            for result_name, metric_dict in local_metric_results.items():
                if len(result_name) > left_width:
                    left_width = len(result_name)
                    for metric_name, metric_value in metric_dict.items():
                        if len(metric_name + ': ' + str(metric_value)) > right_width:
                            right_width = len(metric_name + ': ' + str(metric_value))

            tab_local_metric_results = PrettyTable(['result', 'local metrics'])
            tab_local_metric_results.align['result'] = "r"
            tab_local_metric_results.align['local metrics'] = "l"
            for result_name, metric_dict in local_metric_results.items():
                concat_metric_lines = ''
                for metric_name, metric_value in metric_dict.items():
                    concat_metric_lines += metric_name
                    concat_metric_lines += ': '
                    concat_metric_lines += str(metric_value)
                    concat_metric_lines += '\n'

                concat_metric_lines = concat_metric_lines[:-1]  # strip last newline
                tab_local_metric_results.add_row([result_name, concat_metric_lines])
                tab_local_metric_results.add_row(['-' * left_width, ('-' * right_width) + '--'])

            tab_local_metric_results.del_row(-1)
            print(tab_local_metric_results)

    @staticmethod
    def export_statistics_and_metrics_as_file(
            statistics: Dict[str, Any],
            overall_metric_results: Dict[str, Any],
            local_metric_results: Dict[str, Dict[str, Any]],
            analysis_name: str, export_dir: str
        ):
        """Writes all collected statistics, overall metric results and local metric results to a file, formatted by a prettytable."""

        file = open(export_dir + '/' + 'emerge-' + 'statistics-metrics' + '.txt', 'w', encoding="utf-8")

        if bool(statistics):
            file.write(f'the following statistics were collected in {analysis_name}\n')
            tab_statistics = PrettyTable(['statistic name', 'value'])
            tab_statistics.align['statistic name'] = "r"
            tab_statistics.align['value'] = "l"

            for name, value in statistics.items():
                tab_statistics.add_row([name, value])

            file.write(tab_statistics.get_string())
            file.write('\n\n')

        if bool(overall_metric_results):
            file.write(f'the following overall metrics were collected in {analysis_name}\n')
            tab_metric_results = PrettyTable(['metric name', 'value'])
            tab_metric_results.align['metric name'] = "r"
            tab_metric_results.align['value'] = "l"

            for name, value in overall_metric_results.items():
                if isinstance(value, dict):
                    values_as_string = ', '.join(str(x) for x in value.values())
                    tab_metric_results.add_row([name, values_as_string])
                elif isinstance(value, str):
                    tab_metric_results.add_row([name, value])
                else:
                    tab_metric_results.add_row([name, round(value, 2)])

            file.write(tab_metric_results.get_string())
            file.write('\n\n')

            # local metrics
            file.write(f'the following local metrics were collected in {analysis_name}\n')

            left_width, right_width = 0, 0
            for result_name, metric_dict in local_metric_results.items():
                if len(result_name) > left_width:
                    left_width = len(result_name)
                    for metric_name, metric_value in metric_dict.items():
                        if len(metric_name + ': ' + str(metric_value)) > right_width:
                            right_width = len(metric_name + ': ' + str(metric_value))

            tab_local_metric_results = PrettyTable(['result', 'local metrics'])
            tab_local_metric_results.align['result'] = "r"
            tab_local_metric_results.align['local metrics'] = "l"
            for result_name, metric_dict in local_metric_results.items():
                concat_metric_lines = ''
                for metric_name, metric_value in metric_dict.items():
                    concat_metric_lines += metric_name
                    concat_metric_lines += ': '
                    concat_metric_lines += str(metric_value)
                    concat_metric_lines += '\n'

                concat_metric_lines = concat_metric_lines[:-1]  # strip last newline
                tab_local_metric_results.add_row([result_name, concat_metric_lines])
                tab_local_metric_results.add_row(['-' * left_width, ('-' * right_width) + '--'])

            tab_local_metric_results.del_row(-1)

            file.write(tab_local_metric_results.get_string())

        file.close()


class JSONExporter:
    def __init__(self):
        ...

    @staticmethod
    def export_statistics_and_metrics(
            statistics: Dict[str, Any],
            overall_metric_results: Dict[str, Any],
            local_metric_results: Dict[str, Dict[str, Any]],
            analysis_name: str, export_dir: str
        ):
        """Exports all collected statistics, overall metric results and local metric results in JSON."""

        if bool(statistics) or bool(overall_metric_results):
            with open(export_dir + '/' + 'emerge-' + 'statistics-and-metrics' + '.json', 'w', encoding="utf-8") as file:
                json_output: Dict[str, Any] = {}
                json_statistics = {}
                json_metrics = {}
                json_local_metrics = {}

                if bool(statistics):
                    for name, value in statistics.items():
                        json_statistics[name] = value

                if bool(overall_metric_results):
                    for name, value in overall_metric_results.items():

                        if isinstance(value, dict):
                            values_as_string = ', '.join(str(x) for x in value.values())
                            json_metrics[name] = values_as_string
                        elif isinstance(value, str):
                            json_metrics[name] = value
                        else:
                            json_metrics[name] = round(value, 2)

                if bool(local_metric_results):
                    for result_name, metric_dict in local_metric_results.items():
                        all_metrics_for_result = {}
                        for metric_name, metric_value in metric_dict.items():
                            all_metrics_for_result[metric_name] = metric_value

                        json_local_metrics[result_name] = all_metrics_for_result

                json_output["analysis-name"] = analysis_name

                if bool(json_statistics):
                    json_output["statistics"] = json_statistics

                if bool(json_metrics):
                    json_output["overall-metrics"] = json_metrics

                if bool(json_local_metrics):
                    json_output["local-metrics"] = json_local_metrics

                json.dump(json_output, file)


class DOTExporter:
    def __init__(self):
        ...

    @staticmethod
    def export_graph_as_dot(graph, export_name, export_dir):
        write_dot(graph, export_dir + '/' + 'emerge-' + export_name + '.dot')


class D3Exporter:
    def __init__(self):
        ...

    # pylint: disable=too-many-statements
    @staticmethod
    def export_d3_force_directed_graph(graph_representations, statistics: Dict[str, Any], overall_metric_results: Dict[str, Any], analysis, export_dir):
        """Exports all given graph representations to a JavaScript syntax ready to be used within a D3 force graph simulation."""

        d3_js_string = ''

        graph_representation: GraphRepresentation
        for _, graph_representation in graph_representations.items():

            graph = graph_representation.digraph
            data = json_graph.node_link_data(graph)

            d3_js_string += 'const ' + graph_representation.graph_type.name.lower() + ' = ' + json.dumps(data)
            json_statistics = {}
            json_metrics = {}

            if bool(statistics):
                for name, value in statistics.items():
                    json_statistics[name] = value

                d3_js_string += '\n'
                d3_js_string += 'const ' + graph_representation.graph_type.name.lower() + '_statistics = '
                d3_js_string += json.dumps(json_statistics)

            if bool(overall_metric_results):
                for name, value in overall_metric_results.items():

                    if isinstance(value, dict):
                        values_as_string = ', '.join(str(x) for x in value.values())
                        json_metrics[name] = values_as_string
                    elif isinstance(value, str):
                        json_metrics[name] = value
                    else:
                        json_metrics[name] = round(value, 2)

                d3_js_string += '\n'
                d3_js_string += 'const ' + graph_representation.graph_type.name.lower() + '_overall_metric_results = '
                d3_js_string += json.dumps(json_metrics)

            # add cluster map of nodes
            cluster_map: Dict[Any, Any] = {}

            # count total sloc since we need it to calculate cluster proportions
            total_sloc = 0

            # now loop over all nodes and create a cluster map helper structure
            for node in data['nodes']:
                node_cluster_id = 0
                
                if graph_representation.graph_type == GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH:
                    if 'metric_entity_result_dependency_graph_louvain-modularity-in-entity' in node:
                        node_cluster_id = node['metric_entity_result_dependency_graph_louvain-modularity-in-entity']

                if graph_representation.graph_type == GraphType.ENTITY_RESULT_INHERITANCE_GRAPH:
                    if 'metric_entity_result_inheritance_graph_louvain-modularity-in-entity' in node:
                        node_cluster_id = node['metric_entity_result_inheritance_graph_louvain-modularity-in-entity']

                if graph_representation.graph_type == GraphType.ENTITY_RESULT_COMPLETE_GRAPH:
                    if 'metric_entity_result_complete_graph_louvain-modularity-in-entity' in node:
                        node_cluster_id = node['metric_entity_result_complete_graph_louvain-modularity-in-entity']

                if graph_representation.graph_type == GraphType.FILE_RESULT_DEPENDENCY_GRAPH or graph_representation.graph_type == GraphType.FILESYSTEM_GRAPH:      
                    if 'metric_file_result_dependency_graph_louvain-modularity-in-file' in node:
                        node_cluster_id = node['metric_file_result_dependency_graph_louvain-modularity-in-file']

                if 'metric_sloc-in-file' in node:
                    total_sloc += node['metric_sloc-in-file']
                elif 'metric_sloc-in-entity' in node:
                    total_sloc += node['metric_sloc-in-entity']

                if node_cluster_id in cluster_map:
                    cluster_map[node_cluster_id].append(node)
                else:
                    cluster_map[node_cluster_id] = []
                    cluster_map[node_cluster_id].append(node)

            # sort cluster map (since it is sorted by key in the js frontend)
            cluster_map = OrderedDict(sorted(cluster_map.items()))

            # add cluster metrics map
            cluster_metrics_map: Dict[Any, Any] = {}

            # eventually create all cluster metrics
            for cluster_id, _ in cluster_map.items():
                cluster_nodes = cluster_map[cluster_id]

                # define cluster key/metric names
                sloc_in_cluster = 0.0
                sloc_proportion_of_total = 0.0
                avg_cluster_fan_in = 0.0
                cluster_fan_in = 0.0
                avg_cluster_fan_out = 0.0
                cluster_fan_out = 0.0
                avg_cluster_methods = 0.0
                cluster_methods = 0.0
                nodes_in_cluster = 0.0

                for node in cluster_nodes:
                    nodes_in_cluster += 1

                    if cluster_id not in cluster_metrics_map:
                        cluster_metrics_map[cluster_id] = {}

                    # sloc
                    if 'metric_sloc-in-file' in node:
                        sloc_in_cluster += node['metric_sloc-in-file']
                    elif 'metric_sloc-in-entity' in node:
                        sloc_in_cluster += node['metric_sloc-in-entity']

                    # fan-in
                    if 'metric_fan-in-dependency-graph' in node:
                        cluster_fan_in += node['metric_fan-in-dependency-graph']
                    elif 'metric_fan-in-inheritance-graph' in node:
                        cluster_fan_in += node['metric_fan-in-inheritance-graph']
                    elif 'metric_fan-in-complete-graph' in node:
                        cluster_fan_in += node['metric_fan-in-complete-graph']

                    # fan-out
                    if 'metric_fan-out-dependency-graph' in node:
                        cluster_fan_out += node['metric_fan-out-dependency-graph']
                    elif 'metric_fan-out-inheritance-graph' in node:
                        cluster_fan_out += node['metric_fan-out-inheritance-graph']
                    elif 'metric_fan-out-complete-graph' in node:
                        cluster_fan_out += node['metric_fan-out-complete-graph']

                    # number of methods
                    if 'metric_number-of-methods-in-file' in node:
                        cluster_methods += node['metric_number-of-methods-in-file']
                    elif 'metric_number-of-methods-in-entity' in node:
                        cluster_methods += node['metric_number-of-methods-in-entity']

                # now add all cluster metrics
                cluster_metrics_map[cluster_id]['nodes_in_cluster'] = str(int(nodes_in_cluster))
                cluster_metrics_map[cluster_id]['sloc_in_cluster'] = str(int(sloc_in_cluster))

                if total_sloc > 0:
                    sloc_proportion_of_total = (sloc_in_cluster / total_sloc) * 100
                    cluster_metrics_map[cluster_id]['% of total sloc'] = format(sloc_proportion_of_total, '.2f')

                if nodes_in_cluster > 0:
                    avg_cluster_fan_in = cluster_fan_in / nodes_in_cluster
                    cluster_metrics_map[cluster_id]['avg_cluster_fan_in'] = format(avg_cluster_fan_in, '.2f')

                    avg_cluster_fan_out = cluster_fan_out / nodes_in_cluster
                    cluster_metrics_map[cluster_id]['avg_cluster_fan_out'] = format(avg_cluster_fan_out, '.2f')

                    avg_cluster_methods = cluster_methods / nodes_in_cluster
                    cluster_metrics_map[cluster_id]['avg_cluster_methods'] = format(avg_cluster_methods, '.2f')

            d3_js_string += '\n'
            d3_js_string += 'const ' + graph_representation.graph_type.name.lower() + '_cluster_metrics_map = '
            d3_js_string += json.dumps(cluster_metrics_map)

            d3_js_string += '\n\n'

        d3_js_string = d3_js_string.replace('-', '_')  # kebab case variable names are evil

        d3_js_string += "const analysis_name = '" + analysis.analysis_name + "'"
        d3_js_string += '\n\n'

        # now export all the appconfig
        
        app_config = {
            'project_name': analysis.project_name,
            'analysis_name': analysis.analysis_name,
            'analysis_date': analysis.analysis_date,
            'emerge_version': analysis.emerge_version,

            'metrics': {
                'radius_multiplication': {
                    'metric_fan_in_dependency_graph': analysis.radius_fan_in,
                    'metric_fan_in_inheritance_graph': analysis.radius_fan_in,
                    'metric_fan_in_complete_graph': analysis.radius_fan_in,

                    'metric_fan_out_dependency_graph': analysis.radius_fan_out,
                    'metric_fan_out_inheritance_graph': analysis.radius_fan_out,
                    'metric_fan_out_complete_graph': analysis.radius_fan_out,

                    'metric_entity_result_dependency_graph_louvain_modularity_in_entity': analysis.radius_louvain,
                    'metric_entity_result_inheritance_graph_louvain_modularity_in_entity': analysis.radius_louvain,
                    'metric_entity_result_complete_graph_louvain_modularity_in_entity': analysis.radius_louvain,
                    'metric_entity_result_dependency_graph_louvain_modularity_in_file': analysis.radius_louvain,

                    'metric_sloc_in_file': analysis.radius_sloc,
                    'metric_sloc_in_entity': analysis.radius_sloc,

                    'metric_number_of_methods_in_file': analysis.radius_number_of_methods,
                    'metric_number_of_methods_in_entity': analysis.radius_number_of_methods
                }
            },
            'heatmap': {
                'metrics': {
                    'active': {
                        'sloc': analysis.heatmap_sloc_active,
                        'fan_out': analysis.heatmap_fan_out_active
                    },
                    'weights': {
                        'sloc': analysis.heatmap_sloc_weight,
                        'fan_out': analysis.heatmap_fan_out_weight
                    }
                },
                'score': {
                    'limit': analysis.heatmap_score_limit,
                    'base': analysis.heatmap_score_base
                }
            }
        }

        d3_js_string += "let analysis_config = "
        d3_js_string += json.dumps(app_config) 

        target_force_graph_subpath = "/html"
        target_graph_subpath = "/resources/js"
        target_export_file_path = export_dir + target_force_graph_subpath + target_graph_subpath + \
            '/' + 'graph_representations' + '_d3_force_graph' + '.js'

        with open(target_export_file_path, 'w', encoding="utf-8") as file:
            file.write(d3_js_string)
