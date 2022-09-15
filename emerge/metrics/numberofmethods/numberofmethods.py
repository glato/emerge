"""
Contains the implementation of the number of methods metric.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, Pattern
from enum import auto
import logging
import re

import coloredlogs

from emerge.analysis import Analysis

# interfaces for inputs
from emerge.abstractresult import AbstractResult, AbstractFileResult, AbstractEntityResult
from emerge.log import Logger

# enums and interface/type of the given metric
from emerge.metrics.abstractmetric import EnumLowerKebabCase
from emerge.metrics.metrics import CodeMetric


LOGGER = Logger(logging.getLogger('metrics'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class NumberOfMethodsMetric(CodeMetric):

    class Keys(EnumLowerKebabCase):
        NUMBER_OF_METHODS_IN_ENTITY = auto()
        NUMBER_OF_METHODS_IN_FILE = auto()
        AVG_NUMBER_OF_METHODS_IN_ENTITY = auto()
        AVG_NUMBER_OF_METHODS_IN_FILE = auto()

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)

        self.regex_patters = {
            "JAVA":       r"\b(?!if|for|while|switch|catch)\b[a-zA-Z\d_]+?\s*?\([a-zA-Z\d\s_,\>\<\?\*\.\[\]]*?\)\s*?\{",
            "KOTLIN":     r"fun\s[a-zA-Z\d_\.]+?\s*?\([a-zA-Z\d\s_,\?\@\>\<\?\*\.\[\]\:]*?\)\s*?.*?(\{|\=)",
            "OBJC":       r"[\-\+]\s*?[a-zA-Z\d_\(\)\:\*\s]+?\s*?\{",
            "SWIFT":      r"func\s*?[a-zA-Z\d_\(\)\:\*\s\-\<\>\?\,\[\]\.]+?\s*?\{",
            "RUBY":       r"(def)\s(.+)",
            "GROOVY":     r"\b(?!if|for|while|switch|catch)\b[a-zA-Z\d_]+?\s*?\([a-zA-Z\d\s_,\>\<\?\*\.\[\]\=\@\']*?\)\s*?\{",
            "JAVASCRIPT": r"(function\s+?)([a-zA-Z\d_\:\*\-\<\>\?\,\[\]\.\s\|\=\$]+?)\(([a-zA-Z\d_\(\)\:\*\s\-\<\>\?\,\[\]\.\|\=\$\/]*?)\)*?[\:]*?\s*?\{",
            "TYPESCRIPT": r"(function\s+?)([a-zA-Z\d_\:\*\-\<\>\?\,\[\]\.\s\|\=\$]+?)\(([a-zA-Z\d_\(\)\:\*\s\-\<\>\?\,\[\]\.\|\=\$\/]*?)\)*?[\:]*?\s*?\{",
            "C":          r"\b(?!if|for|while|switch)\b[a-zA-Z\d_]+?\s*?\([a-zA-Z\d\s_,\*]*?\)\s*?\{",
            "CPP":        r"\b(?!if|for|while|switch)\b[a-zA-Z\d\_\:\<\>\*\&]+?\s*?\([\(a-zA-Z\d\s_,\*&:]*?\)\s*?\w+\s*?\{",
            "PY":         r"(def)\s.+(.+):",
            "GO":         r"func\s*?[a-zA-Z\d_\(\)\:\*\s\-\<\>\?\,\[\]\.]+?\s*?\{",
        }

        self.compiled_re: Dict[str, Pattern] = {}
        self._compile()

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        self._calculate_local_metric_data(results)
        self._calculate_global_metric_data(results)

    def _compile(self):
        for name, pattern in self.regex_patters.items():
            self.compiled_re[name] = re.compile(pattern)

    def _calculate_local_metric_data(self, results: Dict[str, AbstractResult]):
        for _, result in results.items():
            LOGGER.debug(f'calculating metric {self.pretty_metric_name} for result {result.unique_name}')

            find_method_expression = self.__get_expression(result)

            LOGGER.debug(f'extracting methods from result {result.scanned_file_name}')
            full_string = " ".join(result.scanned_tokens)
            number_of_methods = len(find_method_expression.findall(full_string))

            if isinstance(result, AbstractFileResult):
                result.metrics[self.Keys.NUMBER_OF_METHODS_IN_FILE.value] = number_of_methods
                self.local_data[result.unique_name] = {self.Keys.NUMBER_OF_METHODS_IN_FILE.value: number_of_methods}

            if isinstance(result, AbstractEntityResult):
                result.metrics[self.Keys.NUMBER_OF_METHODS_IN_ENTITY.value] = number_of_methods
                self.local_data[result.unique_name] = {self.Keys.NUMBER_OF_METHODS_IN_ENTITY.value: number_of_methods}

            LOGGER.debug(f'calculation done, updated metric data of {result.unique_name}: {result.metrics=}')

    def _calculate_global_metric_data(self, results: Dict[str, AbstractResult]):
        LOGGER.debug(f'calculating average method count {self.metric_name}...')

        entity_results = {k: v for (k, v) in results.items() if isinstance(v, AbstractEntityResult)}
        file_results = {k: v for (k, v) in results.items() if isinstance(v, AbstractFileResult)}

        if len(file_results) > 0:
            total_method_count, total_files = 0, 0
            for _, file_result in file_results.items():
                total_files += 1
                total_method_count += file_result.metrics[self.Keys.NUMBER_OF_METHODS_IN_FILE.value]

            average_methods_in_file = total_method_count / total_files
            self.overall_data[self.Keys.AVG_NUMBER_OF_METHODS_IN_FILE.value] = average_methods_in_file
            LOGGER.debug(f'average method count per file: {average_methods_in_file}')

        if len(entity_results) > 0:
            total_method_count, total_entities = 0, 0
            for _, entity_result in entity_results.items():
                total_entities += 1
                total_method_count += entity_result.metrics[self.Keys.NUMBER_OF_METHODS_IN_ENTITY.value]

            average_methods_in_entity = total_method_count / total_entities
            self.overall_data[self.Keys.AVG_NUMBER_OF_METHODS_IN_ENTITY.value] = average_methods_in_entity
            LOGGER.debug(f'average method count per entity: {average_methods_in_entity}')

    def __get_expression(self, result: AbstractResult) -> Pattern:
        return self.compiled_re[result.scanned_language.name]
