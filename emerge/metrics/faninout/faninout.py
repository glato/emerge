"""
Contains the implementation of the fan-in fan-out graph metric.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict
from enum import auto

import logging
import coloredlogs

from networkx import DiGraph

from emerge.abstractresult import AbstractResult
from emerge.log import Logger
from emerge.graph import GraphRepresentation, GraphType

# enums and superclass of the given metric
from emerge.metrics.abstractmetric import EnumLowerKebabCase
from emerge.metrics.metrics import GraphMetric


LOGGER = Logger(logging.getLogger('metrics'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class FanInOutMetric(GraphMetric):

    class Keys(EnumLowerKebabCase):
        FAN_IN_DEPENDENCY_GRAPH = auto()
        FAN_OUT_DEPENDENCY_GRAPH = auto()
        AVG_FAN_IN_DEPENDENCY_GRAPH = auto()
        AVG_FAN_OUT_DEPENDENCY_GRAPH = auto()
        MAX_FAN_IN_DEPENDENCY_GRAPH = auto()
        MAX_FAN_OUT_DEPENDENCY_GRAPH = auto()
        MAX_FAN_IN_NAME_DEPENDENCY_GRAPH = auto()
        MAX_FAN_OUT_NAME_DEPENDENCY_GRAPH = auto()

        FAN_IN_INHERITANCE_GRAPH = auto()
        FAN_OUT_INHERITANCE_GRAPH = auto()
        AVG_FAN_IN_INHERITANCE_GRAPH = auto()
        AVG_FAN_OUT_INHERITANCE_GRAPH = auto()
        MAX_FAN_IN_INHERITANCE_GRAPH = auto()
        MAX_FAN_OUT_INHERITANCE_GRAPH = auto()
        MAX_FAN_IN_NAME_INHERITANCE_GRAPH = auto()
        MAX_FAN_OUT_NAME_INHERITANCE_GRAPH = auto()

        FAN_IN_COMPLETE_GRAPH = auto()
        FAN_OUT_COMPLETE_GRAPH = auto()
        AVG_FAN_IN_COMPLETE_GRAPH = auto()
        AVG_FAN_OUT_COMPLETE_GRAPH = auto()
        MAX_FAN_IN_COMPLETE_GRAPH = auto()
        MAX_FAN_OUT_COMPLETE_GRAPH = auto()
        MAX_FAN_IN_NAME_COMPLETE_GRAPH = auto()
        MAX_FAN_OUT_NAME_COMPLETE_GRAPH = auto()

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        self._calculate_metric_data()

    def _calculate_metric_data(self):
        metric_keys: Dict[str, str] = {}
        instances = [x for x in [self.dependency_graph_representation, self.inheritance_graph_representation, self.complete_graph_representation] if x]
        graph_instance: GraphRepresentation

        for graph_instance in instances:
            digraph: DiGraph = graph_instance.digraph
            average_fan_in, average_fan_out = 0, 0

            for node_with_unique_result_name in digraph.nodes:

                fan_in = digraph.in_degree(node_with_unique_result_name)
                fan_out = digraph.out_degree(node_with_unique_result_name)

                LOGGER.debug(f'fan-in for {node_with_unique_result_name}: {fan_in}')
                LOGGER.debug(f'fan-out for {node_with_unique_result_name}: {fan_out}')

                if graph_instance.graph_type == GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH or graph_instance.graph_type == GraphType.FILE_RESULT_DEPENDENCY_GRAPH:
                    metric_keys = {'fan-in': self.Keys.FAN_IN_DEPENDENCY_GRAPH.value, 'fan-out': self.Keys.FAN_OUT_DEPENDENCY_GRAPH.value,
                                   'avg-fan-in': self.Keys.AVG_FAN_IN_DEPENDENCY_GRAPH.value, 'avg-fan-out': self.Keys.AVG_FAN_OUT_DEPENDENCY_GRAPH.value}
                                   
                if graph_instance.graph_type == GraphType.ENTITY_RESULT_INHERITANCE_GRAPH:
                    metric_keys = {'fan-in': self.Keys.FAN_IN_INHERITANCE_GRAPH.value, 'fan-out': self.Keys.FAN_OUT_INHERITANCE_GRAPH.value,
                                   'avg-fan-in': self.Keys.AVG_FAN_IN_INHERITANCE_GRAPH.value, 'avg-fan-out': self.Keys.AVG_FAN_OUT_INHERITANCE_GRAPH.value}

                if graph_instance.graph_type == GraphType.ENTITY_RESULT_COMPLETE_GRAPH:
                    metric_keys = {'fan-in': self.Keys.FAN_IN_COMPLETE_GRAPH.value, 'fan-out': self.Keys.FAN_OUT_COMPLETE_GRAPH.value,
                                   'avg-fan-in': self.Keys.AVG_FAN_IN_COMPLETE_GRAPH.value, 'avg-fan-out': self.Keys.AVG_FAN_OUT_COMPLETE_GRAPH.value}

                data = {metric_keys['fan-in']: fan_in, metric_keys['fan-out']: fan_out}
                if node_with_unique_result_name in self.local_data:
                    self.local_data[node_with_unique_result_name].update(data)
                else:
                    self.local_data[node_with_unique_result_name] = data

                average_fan_in += fan_in
                average_fan_out += fan_out

            try:

                average_fan_in /= digraph.number_of_nodes()
                average_fan_out /= digraph.number_of_nodes()

                avg_data = {metric_keys['avg-fan-in']: average_fan_in,
                            metric_keys['avg-fan-out']: average_fan_out}

                LOGGER.debug(f'average fan-in in {graph_instance.graph_type.name}: {average_fan_in}')
                LOGGER.debug(f'average fan-out in {graph_instance.graph_type.name}: {average_fan_out}')

                biggest_fan_in = sorted(digraph.in_degree, key=lambda x: x[1], reverse=True)[0]
                biggest_fan_in_name, biggest_fan_in_degree = biggest_fan_in[0], biggest_fan_in[1]

                biggest_fan_out = sorted(digraph.out_degree, key=lambda x: x[1], reverse=True)[0]
                biggest_fan_out_name, biggest_fan_out_degree = biggest_fan_out[0], biggest_fan_out[1]

                if graph_instance.graph_type == GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH or graph_instance.graph_type == GraphType.FILE_RESULT_DEPENDENCY_GRAPH:
                    avg_data[self.Keys.MAX_FAN_IN_DEPENDENCY_GRAPH.value] = biggest_fan_in_degree
                    avg_data[self.Keys.MAX_FAN_IN_NAME_DEPENDENCY_GRAPH.value] = biggest_fan_in_name
                    avg_data[self.Keys.MAX_FAN_OUT_DEPENDENCY_GRAPH.value] = biggest_fan_out_degree
                    avg_data[self.Keys.MAX_FAN_OUT_NAME_DEPENDENCY_GRAPH.value] = biggest_fan_out_name

                if graph_instance.graph_type == GraphType.ENTITY_RESULT_INHERITANCE_GRAPH:
                    avg_data[self.Keys.MAX_FAN_IN_INHERITANCE_GRAPH.value] = biggest_fan_in_degree
                    avg_data[self.Keys.MAX_FAN_IN_NAME_INHERITANCE_GRAPH.value] = biggest_fan_in_name
                    avg_data[self.Keys.MAX_FAN_OUT_INHERITANCE_GRAPH.value] = biggest_fan_out_degree
                    avg_data[self.Keys.MAX_FAN_OUT_NAME_INHERITANCE_GRAPH.value] = biggest_fan_out_name

                if graph_instance.graph_type == GraphType.ENTITY_RESULT_COMPLETE_GRAPH:
                    avg_data[self.Keys.MAX_FAN_IN_COMPLETE_GRAPH.value] = biggest_fan_in_degree
                    avg_data[self.Keys.MAX_FAN_IN_NAME_COMPLETE_GRAPH.value] = biggest_fan_in_name
                    avg_data[self.Keys.MAX_FAN_OUT_COMPLETE_GRAPH.value] = biggest_fan_out_degree
                    avg_data[self.Keys.MAX_FAN_OUT_NAME_COMPLETE_GRAPH.value] = biggest_fan_out_name

                self.overall_data.update(avg_data)

            except ZeroDivisionError:
                LOGGER.error('graph representation has no nodes, skipping average metrics')
