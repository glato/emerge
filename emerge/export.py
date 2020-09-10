"""
Contains all classes related to exporters, e.g. GraphExporter.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, Any

from emerge.logging import Logger

import networkx as nx
from networkx.readwrite import json_graph
from networkx.drawing.nx_agraph import write_dot
from networkx.readwrite import json_graph

from emerge.graph import GraphRepresentation

from prettytable import PrettyTable
import json
import coloredlogs
import logging

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
    def export_statistics_and_metrics_to_console(statistics: Dict[str, Any], overall_metric_results: Dict[str, Any], local_metric_results: Dict[str, Dict[str, Any]], analysis_name: str):
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
    def export_statistics_and_metrics_as_file(statistics: Dict[str, Any], overall_metric_results: Dict[str, Any], local_metric_results: Dict[str, Dict[str, Any]], analysis_name: str, export_dir: str):
        """Writes all collected statistics, overall metric results and local metric results to a file, formatted by a prettytable."""

        file = open(export_dir + '/' + 'emerge-' + 'statistics-metrics' + '.txt', 'w')

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
    def export_statistics_and_metrics(statistics: Dict[str, Any], overall_metric_results: Dict[str, Any], local_metric_results: Dict[str, Dict[str, Any]], analysis_name: str, export_dir: str):
        """Exports all collected statistics, overall metric results and local metric results in JSON."""

        if bool(statistics) or bool(overall_metric_results):
            with open(export_dir + '/' + 'emerge-' + 'statistics-and-metrics' + '.json', 'w') as file:
                json_output = {}
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

    @staticmethod
    def export_d3_force_directed_graph(graph_representations, statistics: Dict[str, Any], overall_metric_results: Dict[str, Any], export_dir):
        """Exports all given graph representations to a JavaScript syntax ready to be used within a D3 force graph simulation."""

        d3_js_string = ''
        graph_representation: GraphRepresentation
        for _, graph_representation in graph_representations.items():

            graph = graph_representation.digraph
            data = json_graph.node_link_data(graph)
            d3_js_string += 'var ' + graph_representation.graph_type.name.lower() + ' = ' + json.dumps(data)
            json_statistics = {}
            json_metrics = {}

            if bool(statistics):
                for name, value in statistics.items():
                    json_statistics[name] = value

                d3_js_string += '\n'
                d3_js_string += 'var ' + graph_representation.graph_type.name.lower() + '_statistics = '
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
                d3_js_string += 'var ' + graph_representation.graph_type.name.lower() + '_overall_metric_results = '
                d3_js_string += json.dumps(json_metrics)

            d3_js_string += '\n\n'

        d3_js_string = d3_js_string.replace('-', '_')  # kebab case variable names are evil

        target_force_graph_subpath = "/force-graph-html"
        target_graph_subpath = "/resources/js"
        target_export_file_path = export_dir + target_force_graph_subpath + target_graph_subpath + \
            '/' + 'graph_representations' + '_d3_force_graph' + '.js'

        with open(target_export_file_path, 'w') as file:
            file.write(d3_js_string)
