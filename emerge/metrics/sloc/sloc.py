"""
Contains the implementation of the source lines of code metric.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import List, Dict
from enum import Enum, auto
import logging

import coloredlogs

from emerge.languages.abstractparser import LanguageType

# interfaces for inputs
#from emerge.analysis import Analysis
from emerge.abstractresult import AbstractResult, AbstractFileResult, AbstractEntityResult
from emerge.log import Logger

# enums and interface/type of the given metric
from emerge.metrics.abstractmetric import EnumLowerKebabCase
from emerge.metrics.metrics import CodeMetric


LOGGER = Logger(logging.getLogger('metrics'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class CommentKeyword(Enum):
    LINE_COMMENT = auto()
    START_BLOCK_COMMENT = auto()
    STOP_BLOCK_COMMENT = auto()


class SLOCCommentType(Enum):
    JAVA = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}
    KOTLIN = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}
    OBJC = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}
    SWIFT = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}
    RUBY = {CommentKeyword.LINE_COMMENT.name: "#", CommentKeyword.START_BLOCK_COMMENT.name: "=begin", CommentKeyword.STOP_BLOCK_COMMENT.name: "=end"}
    GROOVY = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}
    JAVASCRIPT = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}
    TYPESCRIPT = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}
    C = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}
    CPP = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}
    PY = {CommentKeyword.LINE_COMMENT.name: "#", CommentKeyword.START_BLOCK_COMMENT.name: '"""', CommentKeyword.STOP_BLOCK_COMMENT.name: '"""'}
    GO = {CommentKeyword.LINE_COMMENT.name: "//", CommentKeyword.START_BLOCK_COMMENT.name: "/*", CommentKeyword.STOP_BLOCK_COMMENT.name: "*/"}


class SourceLinesOfCodeMetric(CodeMetric):

    class Keys(EnumLowerKebabCase):
        SLOC_IN_ENTITY = auto()
        SLOC_IN_FILE = auto()
        AVG_SLOC_IN_ENTITY = auto()
        AVG_SLOC_IN_FILE = auto()
        TOTAL_SLOC_IN_FILES = auto()
        TOTAL_SLOC_IN_ENTITIES = auto()

    # def __init__(self, analysis: Analysis):
    #     super().__init__(analysis)

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        self._calculate_local_metric_data(results)
        self._calculate_global_metric_data(results)

    def _calculate_local_metric_data(self, results: Dict[str, AbstractResult]):
        for _, result in results.items():
            LOGGER.debug(f'calculating metric {self.pretty_metric_name} for result {result.unique_name}')
            comment_types = self.__get_comment_types(result)
            sloc = self._count_sloc(result.scanned_tokens,
                                    comment_types[CommentKeyword.LINE_COMMENT.name],
                                    comment_types[CommentKeyword.START_BLOCK_COMMENT.name],
                                    comment_types[CommentKeyword.STOP_BLOCK_COMMENT.name])

            if isinstance(result, AbstractFileResult):
                result.metrics[self.Keys.SLOC_IN_FILE.value] = sloc
                self.local_data[result.unique_name] = {self.Keys.SLOC_IN_FILE.value: sloc}

            if isinstance(result, AbstractEntityResult):
                result.metrics[self.Keys.SLOC_IN_ENTITY.value] = sloc
                self.local_data[result.unique_name] = {self.Keys.SLOC_IN_ENTITY.value: sloc}

            LOGGER.debug(f'calculation done, updated metric data of {result.unique_name}: {result.metrics=}')

    def _calculate_global_metric_data(self, results: Dict[str, AbstractResult]):
        entity_results = {k: v for (k, v) in results.items() if isinstance(v, AbstractEntityResult)}
        file_results = {k: v for (k, v) in results.items() if isinstance(v, AbstractFileResult)}

        if len(file_results) > 0:
            total_sloc_count, total_files = 0, 0
            for _, file_result in file_results.items():
                total_files += 1
                total_sloc_count += file_result.metrics[self.Keys.SLOC_IN_FILE.value]

            average_sloc_in_file = total_sloc_count / total_files
            self.overall_data[self.Keys.AVG_SLOC_IN_FILE.value] = average_sloc_in_file
            self.overall_data[self.Keys.TOTAL_SLOC_IN_FILES.value] = total_sloc_count
            LOGGER.debug(f'total/average sloc per file: {total_sloc_count}/{average_sloc_in_file}')

        if len(entity_results) > 0:
            total_sloc_count, total_entities = 0, 0
            for _, entity_result in entity_results.items():
                total_entities += 1
                total_sloc_count += entity_result.metrics[self.Keys.SLOC_IN_ENTITY.value]

            average_sloc_in_entity = total_sloc_count / total_entities
            self.overall_data[self.Keys.AVG_SLOC_IN_ENTITY.value] = average_sloc_in_entity
            self.overall_data[self.Keys.TOTAL_SLOC_IN_ENTITIES.value] = total_sloc_count
            LOGGER.debug(f'average sloc per entity: {total_sloc_count}/{average_sloc_in_entity}')

    def _count_sloc(self, list_of_tokens: List[str], line_comment: str, start_block_comment: str, stop_block_comment: str) -> int:
        source = " ".join(list_of_tokens)
        source_lines = source.splitlines()
        source_lines_without_comments = []
        active_block_comment = False

        for line in source_lines:
            # starting a block comment
            if start_block_comment in line and stop_block_comment not in line:
                active_block_comment = True
                continue
            # stopping a block comment
            if start_block_comment not in line and stop_block_comment in line:
                active_block_comment = False
                continue
            # one line block comment
            if start_block_comment in line and stop_block_comment in line:
                continue
            # regular line comment
            if line.strip().startswith(line_comment):
                continue

            if not active_block_comment and line.strip():
                source_lines_without_comments.append(line)

        return len(source_lines_without_comments)

    def __get_comment_types(self, result: AbstractResult):
        if result.scanned_language == LanguageType.C:
            return SLOCCommentType.C.value
        if result.scanned_language == LanguageType.CPP:
            return SLOCCommentType.CPP.value
        if result.scanned_language == LanguageType.GROOVY:
            return SLOCCommentType.GROOVY.value
        if result.scanned_language == LanguageType.JAVA:
            return SLOCCommentType.JAVA.value
        if result.scanned_language == LanguageType.JAVASCRIPT:
            return SLOCCommentType.JAVASCRIPT.value
        if result.scanned_language == LanguageType.TYPESCRIPT:
            return SLOCCommentType.TYPESCRIPT.value
        if result.scanned_language == LanguageType.KOTLIN:
            return SLOCCommentType.KOTLIN.value
        if result.scanned_language == LanguageType.OBJC:
            return SLOCCommentType.OBJC.value
        if result.scanned_language == LanguageType.RUBY:
            return SLOCCommentType.RUBY.value
        if result.scanned_language == LanguageType.SWIFT:
            return SLOCCommentType.SWIFT.value
        if result.scanned_language == LanguageType.PY:
            return SLOCCommentType.PY.value
        if result.scanned_language == LanguageType.GO:
            return SLOCCommentType.GO.value
