"""
Contains an implemetation of a whitespace complexity metric as an alternative to a SLOC metric.
The implementation is borrowed & adjusted from Adam Tornhill | http://www.adamtornhill.com/code/crimescenetools.htm
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict
from enum import auto

import re
import logging
import coloredlogs

# interfaces for inputs
from emerge.analysis import Analysis
from emerge.abstractresult import AbstractResult
from emerge.log import Logger

# enums and interface/type of the given metric
from emerge.metrics.abstractmetric import EnumLowerKebabCase
from emerge.metrics.metrics import CodeMetric

LOGGER = Logger(logging.getLogger('metrics'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)

class WhitespaceMetric(CodeMetric):
    """Provides a code metric based on counting whitespace characters."""

    class Keys(EnumLowerKebabCase):
        WS_COMPLEXITY_IN_FILE = auto()

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)

        self.leading_tabs_expr = re.compile(r'^(\t+)')
        self.leading_spaces_expr = re.compile(r'^( +)')
        self.empty_line_expr = re.compile(r'^\s*$')

    @property
    def pretty_metric_name(self) -> str:
        return 'whitespace metric'
    
    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        for _, result in results.items():
            ws_complexity = sum(self.calculate_complexity_in(result.source))
            result.metrics[self.Keys.WS_COMPLEXITY_IN_FILE.value] = ws_complexity
            self.local_data[result.unique_name] = {self.Keys.WS_COMPLEXITY_IN_FILE.value: ws_complexity}

    def calulate_from_source(self, source: str) -> float:
        return sum(self.calculate_complexity_in(source))

    ### implementation borrowed from Adam Tornhill

    def n_log_tabs(self, line):
        pattern = re.compile(r' +')
        wo_spaces = re.sub(pattern, '', line)
        match = self.leading_tabs_expr.search(wo_spaces)
        if match:
            tabs = match.group()
            return len(tabs)
        return 0
    
    def n_log_spaces(self, line):
        pattern = re.compile(r'\t+')
        wo_tabs = re.sub(pattern, '', line)
        match = self.leading_spaces_expr.search(wo_tabs)
        if match:
            spaces = match.group()
            return len(spaces)
        return 0
    
    def contains_code(self, line):
        return not self.empty_line_expr.match(line)
		
    def complexity_of(self, line):
        return self.n_log_tabs(line) + (self.n_log_spaces(line) / 4) # hardcoded indentation

    def calculate_complexity_in(self, source):
        return [self.complexity_of(line) for line in source.split("\n") if self.contains_code(line)]
