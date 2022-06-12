"""
Contains an implementation of the louvain modularity graph metric.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, Any
from enum import auto
import logging
import coloredlogs

from networkx import DiGraph
import community as community_louvain

from emerge.abstractresult import AbstractResult
from emerge.results import FileResult, EntityResult
from emerge.log import Logger
from emerge.graph import GraphRepresentation, GraphType

# enums and superclass of the given metric
from emerge.metrics.abstractmetric import EnumLowerKebabCase
from emerge.metrics.metrics import GraphMetric


LOGGER = Logger(logging.getLogger('metrics'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class LouvainModularityMetric(GraphMetric):

    class Keys(EnumLowerKebabCase):
        LOUVAIN_MODULARITY_DEPENDENCY_GRAPH = auto()
        LOUVAIN_MODULARITY_INHERITANCE_GRAPH = auto()
        LOUVAIN_MODULARITY_COMPLETE_GRAPH = auto()
        LOUVAIN_COMMUNITIES_DEPENDENCY_GRAPH = auto()
        LOUVAIN_COMMUNITIES_INHERITANCE_GRAPH = auto()
        LOUVAIN_COMMUNITIES_COMPLETE_GRAPH = auto()
        LOUVAIN_BIGGEST_COMMUNITIES_DEPENDENCY_GRAPH = auto()
        LOUVAIN_BIGGEST_COMMUNITIES_INHERITANCE_GRAPH = auto()
        LOUVAIN_BIGGEST_COMMUNITIES_COMPLETE_GRAPH = auto()
        LOUVAIN_MODULARITY_IN_FILE = auto()
        LOUVAIN_MODULARITY_IN_ENTITY = auto()

        LOUVAIN_MODULARITY_FILE_DEPENDENCY_GRAPH = auto()
        LOUVAIN_MODULARITY_ENTITY_DEPENDENCY_GRAPH = auto()
        LOUVAIN_MODULARITY_ENTITY_INHERITANCE_GRAPH = auto()
        LOUVAIN_MODULARITY_ENTITY_COMPLETE_GRAPH = auto()

    # def __init__(self, analysis, graph_representations: Dict):
    #     super().__init__(analysis, graph_representations)

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        self._calculate_metric_data(results)

    def _calculate_metric_data(self, results: Dict[str, AbstractResult]):
        instances = [x for x in [self.dependency_graph_representation, self.inheritance_graph_representation, self.complete_graph_representation] if x]
        graph_instance: GraphRepresentation

        for graph_instance in instances:
            digraph: DiGraph = graph_instance.digraph
            undirected_graph = digraph.to_undirected()

            graph_type_name = graph_instance.graph_type.name

            try:
                optimization_runs = 5
                sum_communities_found, sum_modularity = 0, 0.0
                sum_biggest_five_community_distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

                for run in range(optimization_runs):

                    partition_by_louvain = community_louvain.best_partition(undirected_graph, resolution=1.5)

                    communities_found = max(partition_by_louvain.values()) + 1
                    modularity = community_louvain.modularity(partition_by_louvain, undirected_graph)

                    sum_communities_found += communities_found
                    sum_modularity += modularity

                    # sort by community size
                    community_sizes = {}
                    for i in range(communities_found):
                        community_sizes[i] = sum(map((i).__eq__, partition_by_louvain.values()))

                    sorted_community_sizes = {k: v for k, v in sorted(community_sizes.items(), key=lambda item: item[1], reverse=True)}
                    biggest_five_communities = {k: sorted_community_sizes[k] for k in list(sorted_community_sizes)[:5]}

                    order = 0
                    for _, size in biggest_five_communities.items():
                        sum_biggest_five_community_distribution[order] += size
                        order += 1

                    # fetch community ids in the last iteration and write metric data
                    if run == optimization_runs - 1:

                        # renumber key/value mappings so that increasing louvain community ids are sorted with descreasing partition sizes
                        sorted_partion_by_louvain = {}

                        # this adds more stability to the non-deterministic partition if e.g. coloring by a fixed input set of colors
                        new_community_id = 0
                        for sorted_community_id in sorted_community_sizes.keys():
                            new_partition = {k: new_community_id for k, v in partition_by_louvain.items() if v == sorted_community_id}
                            sorted_partion_by_louvain.update(new_partition)
                            new_community_id += 1

                        for node_name, _ in sorted_partion_by_louvain.items():
                            if node_name in results:
                                result = results[node_name]

                                if isinstance(result, FileResult):    
                                    key = (graph_type_name + '_' + self.Keys.LOUVAIN_MODULARITY_IN_FILE.value).lower()
                                    result.metrics[key] = sorted_partion_by_louvain[node_name]
                                    local_data_graph_type_modularity = {}
                                    local_data_graph_type_modularity = {key: sorted_partion_by_louvain[node_name]}
                                    if result.unique_name in self.local_data:
                                        self.local_data[result.unique_name].update(local_data_graph_type_modularity)
                                    else:
                                        self.local_data[result.unique_name] = local_data_graph_type_modularity

                                elif isinstance(result, EntityResult):
                                    key = (graph_type_name + '_' + self.Keys.LOUVAIN_MODULARITY_IN_ENTITY.value).lower()
                                    result.metrics[key] = sorted_partion_by_louvain[node_name]
                                    local_data_graph_type_modularity = {}
                                    local_data_graph_type_modularity = {key: sorted_partion_by_louvain[node_name]}
                                    if result.unique_name in self.local_data:
                                        self.local_data[result.unique_name].update(local_data_graph_type_modularity)
                                    else:
                                        self.local_data[result.unique_name] = local_data_graph_type_modularity

                            else:  # if it's not in results, it must be a dependency outside of the analysis
                                if graph_instance.graph_type == GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH or \
                                        graph_instance.graph_type == GraphType.ENTITY_RESULT_INHERITANCE_GRAPH or \
                                        graph_instance.graph_type == GraphType.ENTITY_RESULT_COMPLETE_GRAPH:

                                    key = (graph_type_name + '_' + self.Keys.LOUVAIN_MODULARITY_IN_ENTITY.value).lower()
                                    local_data_graph_type_modularity = {}
                                    local_data_graph_type_modularity = {key: sorted_partion_by_louvain[node_name]}
                                    if node_name in self.local_data:
                                        self.local_data[node_name].update(local_data_graph_type_modularity)
                                    else:
                                        self.local_data[node_name] = local_data_graph_type_modularity

                                elif graph_instance.graph_type == GraphType.FILE_RESULT_DEPENDENCY_GRAPH or \
                                        graph_instance.graph_type == GraphType.FILESYSTEM_GRAPH:

                                    key = (graph_type_name + '_' + self.Keys.LOUVAIN_MODULARITY_IN_FILE.value).lower()
                                    local_data_graph_type_modularity = {}
                                    local_data_graph_type_modularity = {key: sorted_partion_by_louvain[node_name]}
                                    if node_name in self.local_data:
                                        self.local_data[node_name].update(local_data_graph_type_modularity)
                                    else:
                                        self.local_data[node_name] = local_data_graph_type_modularity

                for index, distribution in sum_biggest_five_community_distribution.items():
                    sum_biggest_five_community_distribution[index] = round((distribution / optimization_runs) / undirected_graph.number_of_nodes(), 2)

                rounded_communities_found = round((sum_communities_found / optimization_runs))
                rounded_modularity = round((sum_modularity / optimization_runs), 2)

                rounded_modularity = max(rounded_modularity, 0)

                metric_keys: Dict[str, Any] = {}
                if graph_instance.graph_type == GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH or graph_instance.graph_type == GraphType.FILE_RESULT_DEPENDENCY_GRAPH:
                    metric_keys = {
                        self.Keys.LOUVAIN_COMMUNITIES_DEPENDENCY_GRAPH.value: rounded_communities_found,
                        self.Keys.LOUVAIN_MODULARITY_DEPENDENCY_GRAPH.value: rounded_modularity,
                        self.Keys.LOUVAIN_BIGGEST_COMMUNITIES_DEPENDENCY_GRAPH.value: sum_biggest_five_community_distribution
                    }

                if graph_instance.graph_type == GraphType.ENTITY_RESULT_INHERITANCE_GRAPH:
                    metric_keys = {
                        self.Keys.LOUVAIN_COMMUNITIES_INHERITANCE_GRAPH.value: rounded_communities_found,
                        self.Keys.LOUVAIN_MODULARITY_INHERITANCE_GRAPH.value: rounded_modularity,
                        self.Keys.LOUVAIN_BIGGEST_COMMUNITIES_INHERITANCE_GRAPH.value: sum_biggest_five_community_distribution
                    }

                if graph_instance.graph_type == GraphType.ENTITY_RESULT_COMPLETE_GRAPH:
                    metric_keys = {
                        self.Keys.LOUVAIN_COMMUNITIES_COMPLETE_GRAPH.value: rounded_communities_found,
                        self.Keys.LOUVAIN_MODULARITY_COMPLETE_GRAPH.value: rounded_modularity,
                        self.Keys.LOUVAIN_BIGGEST_COMMUNITIES_COMPLETE_GRAPH.value: sum_biggest_five_community_distribution
                    }

                self.overall_data.update(metric_keys)
            
            except Exception as ex: # pylint: disable=broad-except
                LOGGER.error(f'something went wrong, skipping metric {self.metric_name}: {ex}')
