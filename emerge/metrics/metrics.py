"""
Defines concrete metrics based on the abstract interfaces to share/hide common code.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Any, Dict, Optional

# interfaces for inputs
from emerge.abstractresult import AbstractResult
from emerge.graph import GraphRepresentation, GraphType
from emerge.core import camel_to_kebab_case, camel_case_to_words

from emerge.metrics.abstractmetric import AbstractGraphMetric, AbstractCodeMetric


class GraphMetric(AbstractGraphMetric):
    def __init__(self, analysis, graph_representations: Dict):
        self._dependency_graph_representaion: Optional[GraphRepresentation] = None
        self._inheritance_graph_representaion: Optional[GraphRepresentation] = None
        self._complete_graph_representaion: Optional[GraphRepresentation] = None
        self._analysis = analysis
        self._local_data: Dict[str, Dict] = {}
        self._overall_data: Dict[str, Any] = {}
        self._init_graph_representations(graph_representations)

    def _init_graph_representations(self, graph_representations: Dict):
        if GraphType.FILE_RESULT_DEPENDENCY_GRAPH.name.lower() in graph_representations.keys():
            self._dependency_graph_representaion = graph_representations[GraphType.FILE_RESULT_DEPENDENCY_GRAPH.name.lower()]

        if GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH.name.lower() in graph_representations.keys():
            self._dependency_graph_representaion = graph_representations[GraphType.ENTITY_RESULT_DEPENDENCY_GRAPH.name.lower()]

        if GraphType.ENTITY_RESULT_INHERITANCE_GRAPH.name.lower() in graph_representations.keys():
            self._inheritance_graph_representaion = graph_representations[GraphType.ENTITY_RESULT_INHERITANCE_GRAPH.name.lower()]

        if GraphType.ENTITY_RESULT_COMPLETE_GRAPH.name.lower() in graph_representations.keys():
            self._complete_graph_representaion = graph_representations[GraphType.ENTITY_RESULT_COMPLETE_GRAPH.name.lower()]

    @property
    def parent_result(self) -> AbstractResult:
        return self._parent_result

    @parent_result.setter
    def parent_result(self, value):
        self._parent_result = value

    @property
    def metric_name(self):
        return camel_to_kebab_case(self.__class__.__name__)

    @property
    def pretty_metric_name(self):
        return camel_case_to_words(self.__class__.__name__)

    @property
    def dependency_graph_representation(self) -> Any:
        return self._dependency_graph_representaion
    
    @dependency_graph_representation.setter
    def dependency_graph_representation(self, value):
        self._dependency_graph_representaion = value

    @property
    def inheritance_graph_representation(self) -> Any:
        return self._inheritance_graph_representaion
    
    @inheritance_graph_representation.setter
    def inheritance_graph_representation(self, value):
        self._inheritance_graph_representaion = value

    @property
    def complete_graph_representation(self) -> Any:
        return self._complete_graph_representaion

    @complete_graph_representation.setter
    def complete_graph_representation(self, value):
        self._complete_graph_representaion = value

    @property
    def analysis(self):
        return self._analysis

    @property
    def local_data(self) -> Dict[str, Dict]:
        return self._local_data

    @property
    def overall_data(self) -> Dict[str, Any]:
        return self._overall_data

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        pass


class CodeMetric(AbstractCodeMetric):
    def __init__(self, analysis):
        self._analysis = analysis
        self._local_data: Dict[str, Dict] = {}
        self._overall_data: Dict[str, Any] = {}

    @property
    def parent_result(self) -> AbstractResult:
        return self._parent_result

    @parent_result.setter
    def parent_result(self, value):
        self._parent_result = value

    @property
    def metric_name(self) -> str:
        return camel_to_kebab_case(self.__class__.__name__)

    @property
    def pretty_metric_name(self) -> str:
        return camel_case_to_words(self.__class__.__name__)

    @property
    def analysis(self):
        return self._analysis

    @property
    def local_data(self) -> Dict[str, Dict]:
        return self._local_data

    @property
    def overall_data(self) -> Dict[str, Any]:
        return self._overall_data

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        ...
