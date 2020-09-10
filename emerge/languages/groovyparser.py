"""
Contains the implementation of the Groovy language parser and a relevant keyword enum.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import pyparsing as pp
from typing import Dict, List
from enum import Enum, unique
import coloredlogs
import logging
from emerge.languages.abstractparser import AbstractParser, AbstractParsingCore, Parser, CoreParsingKeyword, LanguageType
from emerge.results import FileResult
from emerge.abstractresult import AbstractResult, AbstractFileResult, AbstractEntityResult
from emerge.logging import Logger
from emerge.statistics import Statistics

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class GroovyParsingKeyword(Enum):
    CLASS = "class"
    OPEN_SCOPE = "{"
    CLOSE_SCOPE = "}"
    INLINE_COMMENT = "//"
    START_BLOCK_COMMENT = "/*"
    STOP_BLOCK_COMMENT = "*/"
    EXTENDS = "extends"
    IMPORT = "import"
    PACKAGE = "package"
    PACKAGE_NAME = "package_name"


class GroovyParser(AbstractParser, AbstractParsingCore):

    def __init__(self):
        self._results: Dict[str, AbstractResult] = {}
        self._token_mappings: Dict[str, str] = {
            ':': ' : ',
            ';': ' ; ',
            '{': ' { ',
            '}': ' } ',
            '(': ' ( ',
            ')': ' ) ',
            '[': ' [ ',
            ']': ' ] ',
            '?': ' ? ',
            '!': ' ! ',
            ',': ' , ',
            '<': ' < ',
            '>': ' > ',
            '"': ' " ',
        }

    @classmethod
    def parser_name(cls) -> str:
        return Parser.GROOVY_PARSER.name

    @property
    def results(self) -> Dict[str, AbstractResult]:
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    def generate_file_result_from_analysis(self, analysis, *, file_name: str, file_content: str) -> None:
        LOGGER.debug(f'generating file results...')
        scanned_tokens = self.preprocess_file_content_and_generate_token_list(file_content)
        file_result = FileResult.create_file_result(analysis, file_name, "", self.parser_name(), LanguageType.GROOVY, scanned_tokens)
        self._add_package_name_to_result(file_result)
        self._add_imports_to_result(file_result)
        self._results[file_result.unique_name] = file_result

    def after_generated_file_results(self, analysis) -> None:
        pass

    def create_unique_entity_name(self, *, entity: AbstractEntityResult) -> None:
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def generate_entity_results_from_analysis(self, analysis):
        LOGGER.debug(f'generating entity results...')
        filtered_results = {k: v for (k, v) in self.results.items() if v.analysis is analysis and isinstance(v, AbstractFileResult)}

        result: AbstractFileResult
        for _, result in filtered_results.items():

            entity_keywords: List[str] = [GroovyParsingKeyword.CLASS.value]
            entity_name = pp.Word(pp.alphanums)
            match_expression = pp.Keyword(GroovyParsingKeyword.CLASS.value) + \
                entity_name.setResultsName(CoreParsingKeyword.ENTITY_NAME.value) + \
                pp.Optional(pp.Keyword(GroovyParsingKeyword.EXTENDS.value) +
                            entity_name.setResultsName(CoreParsingKeyword.INHERITED_ENTITY_NAME.value)) + \
                pp.SkipTo(pp.FollowedBy(GroovyParsingKeyword.OPEN_SCOPE.value))

            comment_keywords: Dict[str, str] = {CoreParsingKeyword.LINE_COMMENT.value: GroovyParsingKeyword.INLINE_COMMENT.value,
                                                CoreParsingKeyword.START_BLOCK_COMMENT.value: GroovyParsingKeyword.START_BLOCK_COMMENT.value, CoreParsingKeyword.STOP_BLOCK_COMMENT.value: GroovyParsingKeyword.STOP_BLOCK_COMMENT.value}
            entity_results = result.generate_entity_results_from_scopes(entity_keywords, match_expression, comment_keywords)

            for entity_result in entity_results:
                self._add_inheritance_to_entity_result(entity_result)
                self._add_imports_to_entity_result(entity_result)
                if entity_result.module_name:
                    self._results[entity_result.module_name + CoreParsingKeyword.DOT.value + entity_result.entity_name] = entity_result
                else:
                    self._results[entity_result.entity_name] = entity_result

    def _add_imports_to_result(self, result: AbstractResult):
        LOGGER.debug(f'extracting imports from file result {result.scanned_file_name}...')
        list_of_words_with_newline_strings = result.scanned_tokens
        source_string_no_comments = self._filter_source_tokens_without_comments(
            list_of_words_with_newline_strings, GroovyParsingKeyword.INLINE_COMMENT.value, GroovyParsingKeyword.START_BLOCK_COMMENT.value, GroovyParsingKeyword.STOP_BLOCK_COMMENT.value)
        filtered_list_no_comments = self.preprocess_file_content_and_generate_token_list_by_mapping(source_string_no_comments, self._token_mappings)

        for _, obj, following in self._gen_word_read_ahead(filtered_list_no_comments):
            if obj == GroovyParsingKeyword.IMPORT.value:
                read_ahead_string = self.create_read_ahead_string(obj, following)

                import_name = pp.Word(pp.alphanums + CoreParsingKeyword.DOT.value + CoreParsingKeyword.ASTERISK.value)
                expression_to_match = pp.Keyword(GroovyParsingKeyword.IMPORT.value) + import_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value)

                try:
                    parsing_result = expression_to_match.parseString(read_ahead_string)
                except Exception as some_exception:
                    result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
                    LOGGER.warning(f'warning: could not parse result {result=}\n{some_exception}')
                    LOGGER.warning(f'next tokens: {[obj] + following[:AbstractParsingCore.Constants.MAX_DEBUG_TOKENS_READAHEAD.value]}')
                    continue

                result.scanned_import_dependencies.append(getattr(parsing_result, CoreParsingKeyword.IMPORT_ENTITY_NAME.value))

                result.analysis.statistics.increment(Statistics.Key.PARSING_HITS)
                LOGGER.debug(f'imported entity found: {getattr(parsing_result, CoreParsingKeyword.IMPORT_ENTITY_NAME.value)} and added to result')

    def _add_imports_to_entity_result(self, entity_result: AbstractEntityResult):
        LOGGER.debug(f'adding imports to entity result...')
        for scanned_import in entity_result.parent_file_result.scanned_import_dependencies:
            last_component_of_import = scanned_import.split(CoreParsingKeyword.DOT.value)[-1]
            if last_component_of_import in entity_result.scanned_tokens and scanned_import not in entity_result.scanned_import_dependencies:
                entity_result.scanned_import_dependencies.append(scanned_import)

    def _add_package_name_to_result(self, result: AbstractResult) -> str:
        LOGGER.debug(f'extracting package name from base result {result.scanned_file_name}...')
        list_of_words_with_newline_strings = result.scanned_tokens
        source_string_no_comments = self._filter_source_tokens_without_comments(
            list_of_words_with_newline_strings, GroovyParsingKeyword.INLINE_COMMENT.value, GroovyParsingKeyword.START_BLOCK_COMMENT.value, GroovyParsingKeyword.STOP_BLOCK_COMMENT.value)
        filtered_list_no_comments = self.preprocess_file_content_and_generate_token_list(source_string_no_comments)

        for _, obj, following in self._gen_word_read_ahead(filtered_list_no_comments):
            if obj == GroovyParsingKeyword.PACKAGE.value:
                read_ahead_string = self.create_read_ahead_string(obj, following)

                package_name = pp.Word(pp.alphanums + CoreParsingKeyword.DOT.value)
                expression_to_match = pp.Keyword(GroovyParsingKeyword.PACKAGE.value) + package_name.setResultsName(GroovyParsingKeyword.PACKAGE_NAME.value)

                try:
                    parsing_result = expression_to_match.parseString(read_ahead_string)
                except:
                    result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
                    LOGGER.warning(f'warning: could not parse result {result=}')
                    LOGGER.warning(f'next tokens: {[obj] + following[:AbstractParsingCore.Constants.MAX_DEBUG_TOKENS_READAHEAD.value]}')
                    continue

                result.module_name = getattr(parsing_result, GroovyParsingKeyword.PACKAGE_NAME.value)

                result.analysis.statistics.increment(Statistics.Key.PARSING_HITS)
                LOGGER.debug(f'package found: {result.module_name} and added to result')

    def _add_inheritance_to_entity_result(self, result: AbstractEntityResult):
        LOGGER.debug(f'extracting inheritance from entity result {result.entity_name}...')
        list_of_words = result.scanned_tokens
        for _, obj, following in self._gen_word_read_ahead(list_of_words):
            if obj == GroovyParsingKeyword.CLASS.value:
                read_ahead_string = self.create_read_ahead_string(obj, following)

                entity_name = pp.Word(pp.alphanums)
                expression_to_match = pp.Keyword(GroovyParsingKeyword.CLASS.value) + entity_name.setResultsName(CoreParsingKeyword.ENTITY_NAME.value) + \
                    pp.Optional(pp.Keyword(GroovyParsingKeyword.EXTENDS.value) + entity_name.setResultsName(CoreParsingKeyword.INHERITED_ENTITY_NAME.value)) + \
                    pp.SkipTo(pp.FollowedBy(GroovyParsingKeyword.OPEN_SCOPE.value))

                try:
                    parsing_result = expression_to_match.parseString(read_ahead_string)
                except Exception as some_exception:
                    result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
                    LOGGER.warning(f'warning: could not parse result {result=}\n{some_exception}')
                    LOGGER.warning(f'next tokens: {obj} {following[:10]}')
                    continue

                if len(parsing_result) > 0:
                    parsing_result = expression_to_match.parseString(read_ahead_string)
                    if getattr(parsing_result, CoreParsingKeyword.INHERITED_ENTITY_NAME.value) is not None and bool(getattr(parsing_result, CoreParsingKeyword.INHERITED_ENTITY_NAME.value)):

                        result.analysis.statistics.increment(Statistics.Key.PARSING_HITS)
                        LOGGER.debug(
                            f'found inheritance entity {getattr(parsing_result, CoreParsingKeyword.INHERITED_ENTITY_NAME.value)} for entity name: {getattr(parsing_result, CoreParsingKeyword.ENTITY_NAME.value)} and added to result')
                        result.scanned_inheritance_dependencies.append(getattr(parsing_result, CoreParsingKeyword.INHERITED_ENTITY_NAME.value))


if __name__ == "__main__":
    LEXER = GroovyParser()
    print(f'{LEXER.results=}')
