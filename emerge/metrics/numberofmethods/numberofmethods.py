"""
Contains the implementation of the number of methods metric.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict
from enum import auto
import coloredlogs
import logging
import re

from emerge.analysis import Analysis

# interfaces for inputs
from emerge.abstractresult import AbstractResult, AbstractFileResult, AbstractEntityResult

# enums and interface/type of the given metric
from emerge.metrics.abstractmetric import EnumLowerKebabCase
from emerge.metrics.metrics import CodeMetric

# logging
from emerge.logging import Logger

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
            "JAVA":       r"(.+)\s+.+\(.*\)(\s*)(.*)(\s*)\{",
            "KOTLIN":     r"(.+)\s+.+\(.*\)(\s*)(.*)(\s*)\{",
            "OBJC":       r"(.+)\s+.+\(.*\)(\s*)(.*)(\s*)\{",
            "SWIFT":      r"(.+)\s+.+\(.*\)(\s*)(.*)(\s*)\{",
            "RUBY":       r"(def)\s(.+)",
            "GROOVY":     r"(.+)\s(.+)\s*.+\(.*\)(\s*)\{",
            "JAVASCRIPT": r"(function)\s(.+)\s*.+\(.*\)(\s*)(.*)(\s*)\{",
            "C":          r"(.+)\s(.+)\s*.+\(.*\)(\s*)\{"
        }

        self.compiled_re = {}
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
            list_of_words = result.scanned_tokens
            full_string = " ".join(list_of_words)

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
            for _, result in file_results.items():
                total_files += 1
                total_method_count += result.metrics[self.Keys.NUMBER_OF_METHODS_IN_FILE.value]

            average_methods_in_file = total_method_count / total_files
            self.overall_data[self.Keys.AVG_NUMBER_OF_METHODS_IN_FILE.value] = average_methods_in_file
            LOGGER.debug(f'average method count per file: {average_methods_in_file}')

        if len(entity_results) > 0:
            total_method_count, total_entities = 0, 0
            for _, result in entity_results.items():
                total_entities += 1
                total_method_count += result.metrics[self.Keys.NUMBER_OF_METHODS_IN_ENTITY.value]

            average_methods_in_entity = total_method_count / total_entities
            self.overall_data[self.Keys.AVG_NUMBER_OF_METHODS_IN_ENTITY.value] = average_methods_in_entity
            LOGGER.debug(f'average method count per entity: {average_methods_in_entity}')

    def __get_expression(self, result: AbstractResult) -> str:
        return self.compiled_re[result.scanned_language.name]