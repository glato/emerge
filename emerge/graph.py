"""
Defines a graph representations, available graph types and relevant calculations.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import logging
import coloredlogs

from typing import List, Dict, Any
from enum import Enum, unique, auto
import networkx as nx
from networkx import DiGraph

from emerge.abstractresult import AbstractFileResult, AbstractEntityResult
from emerge.logging import Logger

LOGGER = Logger(logging.getLogger('graph'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class GraphType(Enum):
    FILE_RESULT_DEPENDENCY_GRAPH = auto()
    FILE_RESULT_INHERITANCE_GRAPH = auto()
    FILE_RESULT_COMPLETE_GRAPH = auto()
    ENTITY_RESULT_DEPENDENCY_GRAPH = auto()
    ENTITY_RESULT_INHERITANCE_GRAPH = auto()
    ENTITY_RESULT_COMPLETE_GRAPH = auto()


class GraphRepresentation:
    """GraphRepresentation contains a networkx directed graph instance, a graph type and methods to construct the corresponding graph.
    """

    def __init__(self, graph_type: GraphType):
        self._digraph: DiGraph = DiGraph()
        self._graph_type: GraphType = graph_type

    @property
    def digraph(self) -> DiGraph:
        return self._digraph

    @property
    def graph_type(self) -> GraphType:
        return self._graph_type

    @digraph.setter
    def digraph(self, value: DiGraph):
        self._digraph = value

    def calculate_dependency_graph_from_results(self, results: List[AbstractFileResult]) -> None:
        """Constructs a dependency graph from a list of abstract file results.

        Args:
            results (List[AbstractFileResult]): A list of objects that subclass AbstractFileResult.
        """
        LOGGER.debug(f'creating dependency graph...')
        for _, result in results.items():
            node_name = result.unique_name

            self._digraph.add_node(node_name)
            dependencies = result.scanned_import_dependencies
            for dependency in dependencies:
                self._digraph.add_node(dependency)
                self._digraph.add_edge(node_name, dependency)

    def calculate_inheritance_graph_from_results(self, results: List[AbstractEntityResult]) -> None:
        """Constructs an inheritance graph from a list of abstract entity results.

        Args:
            results (List[AbstractEntityResult]): A list of objects that subclass AbstractEntityResult.
        """
        LOGGER.debug(f'creating inheritance graph...')
        for _, result in results.items():
            node_name = result.unique_name

            self._digraph.add_node(node_name)
            inheritance_dependencies = result.scanned_inheritance_dependencies
            for inheritance_dependency in inheritance_dependencies:
                self._digraph.add_node(inheritance_dependency)
                self._digraph.add_edge(node_name, inheritance_dependency)

    def calculate_complete_graph(self, *, dependency_graph_repr: 'GraphRepresentation', inheritance_graph_repr: 'GraphRepresentation') -> None:
        """Constructs a *complete graph*, which is defined as the composition/union of both dependency and inheritance graph.

        Args:
            dependency_graph_repr (GraphRepresentation): A dependency graph representation.
            inheritance_graph_repr (GraphRepresentation): An inheritance graph representation.
        """
        LOGGER.debug(f'creating complete graph...')
        self._digraph = nx.compose(dependency_graph_repr.digraph, inheritance_graph_repr.digraph)

    def add_local_metric_results_to_graph_nodes(self, metric_results: Dict[str, Dict[str, Any]]) -> None:
        """Adds/maps local metric results to graph nodes.
        """
        nodes = self._digraph.nodes
        graph = self._digraph

        for node in nodes:
            if node in metric_results.keys():
                metric_dict = metric_results[node]
                for name, value in metric_dict.items():
                    graph.nodes[node][name] = value
