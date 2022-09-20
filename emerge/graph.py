"""
Defines a graph representations, available graph types and relevant calculations.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, Any, Optional
from enum import Enum, unique, auto

import logging
import coloredlogs

import networkx as nx
from networkx import DiGraph

from emerge.log import Logger

LOGGER = Logger(logging.getLogger('graph'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class GraphType(Enum):
    """Small enum class to represent a type of a GraphRepresentation. 
    """
    FILE_RESULT_DEPENDENCY_GRAPH = auto()
    ENTITY_RESULT_DEPENDENCY_GRAPH = auto()
    ENTITY_RESULT_INHERITANCE_GRAPH = auto()
    ENTITY_RESULT_COMPLETE_GRAPH = auto()
    FILESYSTEM_GRAPH = auto()

@unique
class GraphFilter(Enum):
    """Small utility enum to filter metrics for graph types.
    """
    DEPENDENCY = auto()
    INHERITANCE = auto()
    COMPLETE = auto()

class GraphRepresentation:
    """GraphRepresentation contains a networkx directed graph instance, a graph type and methods to construct the corresponding graph.
    """

    def __init__(self, graph_type: GraphType):
        self._digraph: DiGraph = DiGraph()
        self._graph_type: GraphType = graph_type
        self.filesystem_nodes: Dict[str, FileSystemNode] = {}

    @property
    def digraph(self) -> DiGraph:
        return self._digraph
    
    @digraph.setter
    def digraph(self, value: DiGraph):
        self._digraph = value

    @property
    def graph_type(self) -> GraphType:
        return self._graph_type

    def calculate_dependency_graph_from_results(self, results: Dict[str, Any]) -> None:
        """Constructs a dependency graph from a list of abstract file results.

        Args:
            results (List[AbstractFileResult]): A list of objects that subclass AbstractFileResult.
        """
        LOGGER.debug('creating dependency graph...')
        for _, result in results.items():
            node_name = result.unique_name
            absolute_name = result.absolute_name
            display_name = result.display_name

            self._digraph.add_node(node_name, absolute_name=absolute_name, display_name=display_name)
            dependencies = result.scanned_import_dependencies
            for dependency in dependencies:
                self._digraph.add_node(dependency, display_name=dependency)
                self._digraph.add_edge(node_name, dependency)

    def calculate_inheritance_graph_from_results(self, results: Dict[str, Any]) -> None:
        """Constructs an inheritance graph from a list of abstract entity results.

        Args:
            results (List[AbstractEntityResult]): A list of objects that subclass AbstractEntityResult.
        """
        LOGGER.debug('creating inheritance graph...')
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
        LOGGER.debug('creating complete graph...')
        self._digraph = nx.compose(dependency_graph_repr.digraph, inheritance_graph_repr.digraph)

    def add_local_metric_results_to_graph_nodes(self, metric_results: Dict[str, Dict[str, Any]]) -> None:
        """Adds/maps local metric results to graph nodes.
        """
        nodes = self._digraph.nodes
        graph = self._digraph

        for node in nodes:

            # clear the filesystem node from the absolute key prefix, since the metrics are calculated with a filename-based key
            if self.graph_type == GraphType.FILESYSTEM_GRAPH:

                current_node = nodes[node]
                if not bool(current_node):
                    continue  # if a file/dependency doesn't physically exits, do not consider it for the filsystem graph
                
                if current_node['directory'] is True:
                    continue  # do not add any metrics to directories

                if node in metric_results.keys():
                    metric_dict = metric_results[node]

                    for name, value in metric_dict.items():
                        if 'entity' not in name:  # do not include any entity metrics in the filesystem graph
                            graph.nodes[node]['metric_' + name] = value

            if self.graph_type == GraphType.FILE_RESULT_DEPENDENCY_GRAPH:
                if node in metric_results.keys():
                    metric_dict = metric_results[node]

                    for name, value in metric_dict.items():
                        if 'entity' not in name:  # do not include any entity metrics in FILE_RESULT graphs
                            graph.nodes[node]['metric_' + name] = value

            if  self.graph_type == GraphType.ENTITY_RESULT_COMPLETE_GRAPH or \
                self.graph_type == GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH or \
                self.graph_type == GraphType.ENTITY_RESULT_INHERITANCE_GRAPH:

                if node in metric_results.keys():
                    metric_dict = metric_results[node]

                    for name, value in metric_dict.items():
                        if 'file' not in name:  # do not include any file metrics in the ENTITY_RESULT graphs  
                            
                            # filter out any metrics that don't belong to the appropriate graph type
                            if self.graph_type == GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH:
                                if GraphFilter.INHERITANCE.name.lower() not in name and GraphFilter.COMPLETE.name.lower() not in name:
                                    graph.nodes[node]['metric_' + name] = value

                            if self.graph_type == GraphType.ENTITY_RESULT_INHERITANCE_GRAPH:
                                if GraphFilter.DEPENDENCY.name.lower() not in name and GraphFilter.COMPLETE.name.lower() not in name:
                                    graph.nodes[node]['metric_' + name] = value

                            if self.graph_type == GraphType.ENTITY_RESULT_COMPLETE_GRAPH:
                                if GraphFilter.INHERITANCE.name.lower() not in name and GraphFilter.DEPENDENCY.name.lower() not in name:
                                    graph.nodes[node]['metric_' + name] = value

@unique
class FileSystemNodeType(Enum):
    FILE = auto()
    DIRECTORY = auto()


class FileSystemNode:
    """Small representation of a filesystem object, e.g. a directory or a file. This class is currently used to build the filesystem graph.
    """

    def __init__(self, node_type: FileSystemNodeType, absolute_name: str, content: Optional[str] = None):
        self.type: FileSystemNodeType = node_type
        self.absolute_name: str = absolute_name
        self.content: Optional[str] = content

    def __hash__(self):
        return hash(self.absolute_name)

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.absolute_name == other.absolute_name
        )

    def __repr__(self):
        return f"{self.absolute_name}"

    def __str__(self):
        return self.absolute_name
