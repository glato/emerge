"""
Contains the implementation of the C language parser and a relevant keyword enum.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict
from enum import Enum, unique
import logging
from pathlib import Path
import os

import pyparsing as pp
import coloredlogs

from emerge.languages.abstractparser import AbstractParser, ParsingMixin, Parser, CoreParsingKeyword, LanguageType
from emerge.results import FileResult
from emerge.abstractresult import AbstractResult, AbstractFileResult, AbstractEntityResult
from emerge.log import Logger
from emerge.stats import Statistics

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class CParsingKeyword(Enum):
    INCLUDE = "#include"
    OPEN_SCOPE = "{"
    CLOSE_SCOPE = "}"
    INLINE_COMMENT = "//"
    START_BLOCK_COMMENT = "/*"
    STOP_BLOCK_COMMENT = "*/"


class CParser(AbstractParser, ParsingMixin):

    def __init__(self):
        self._results: Dict[str, AbstractResult] = {}
        self._token_mappings: Dict[str, str] = {
            ':': ' : ',
            ';': ' ; ',
            '{': ' { ',
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
            '"': ' " '
        }

    @classmethod
    def parser_name(cls) -> str:
        return Parser.C_PARSER.name

    @classmethod
    def language_type(cls) -> str:
        return LanguageType.C.name

    @property
    def results(self) -> Dict[str, AbstractResult]:
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    def generate_file_result_from_analysis(self, analysis, *, file_name: str, full_file_path: str, file_content: str) -> None:
        LOGGER.debug('generating file results...')
        scanned_tokens = self.preprocess_file_content_and_generate_token_list_by_mapping(file_content, self._token_mappings)

        # make sure to create unique names by using the relative analysis path as a base for the result
        parent_analysis_source_path = f"{Path(analysis.source_directory).parent}/"
        relative_file_path_to_analysis = full_file_path.replace(parent_analysis_source_path, "")

        file_result = FileResult.create_file_result(
            analysis=analysis,
            scanned_file_name=file_name,
            relative_file_path_to_analysis=relative_file_path_to_analysis,
            absolute_name=full_file_path,
            display_name=file_name,
            module_name="",
            scanned_by=self.parser_name(),
            scanned_language=LanguageType.C,
            scanned_tokens=scanned_tokens,
            preprocessed_source=""
        )

        self._add_package_name_to_result(file_result)
        self._add_imports_to_result(file_result, analysis)
        self._results[file_result.unique_name] = file_result

    def after_generated_file_results(self, analysis) -> None:
        pass

    def generate_entity_results_from_analysis(self, analysis):
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def create_unique_entity_name(self, entity: AbstractEntityResult) -> None:
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def _add_imports_to_result(self, result: AbstractFileResult, analysis):
        LOGGER.debug(f'extracting imports from file result {result.scanned_file_name}...')
        list_of_words_with_newline_strings = result.scanned_tokens
        
        source_string_no_comments = self._filter_source_tokens_without_comments(
            list_of_words_with_newline_strings,
            CParsingKeyword.INLINE_COMMENT.value,
            CParsingKeyword.START_BLOCK_COMMENT.value,
            CParsingKeyword.STOP_BLOCK_COMMENT.value
        )

        filtered_list_no_comments = self.preprocess_file_content_and_generate_token_list_by_mapping(source_string_no_comments, self._token_mappings)

        for _, obj, following in self._gen_word_read_ahead(filtered_list_no_comments):
            if obj == CParsingKeyword.INCLUDE.value:
                read_ahead_string = self.create_read_ahead_string(obj, following)

                include_name = pp.Word(pp.alphanums + CoreParsingKeyword.DOT.value + CoreParsingKeyword.SLASH.value +
                                       CoreParsingKeyword.DOUBLE_QUOTE.value + CoreParsingKeyword.UNDERSCORE.value + CoreParsingKeyword.DASH.value)

                expression_to_match = pp.Keyword(CParsingKeyword.INCLUDE.value) + \
                    pp.ZeroOrMore(pp.Suppress(CoreParsingKeyword.OPENING_ANGLE_BRACKET.value) |
                                  pp.Suppress(CoreParsingKeyword.CLOSING_ANGLE_BRACKET.value) |
                                  pp.Suppress(CoreParsingKeyword.DOUBLE_QUOTE.value)) + \
                    include_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value)

                try:
                    parsing_result = expression_to_match.parseString(read_ahead_string)
                except pp.ParseException as exception:
                    result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
                    LOGGER.warning(f'warning: could not parse result {result=}\n{exception}')
                    LOGGER.warning(f'next tokens: {[obj] + following[:ParsingMixin.Constants.MAX_DEBUG_TOKENS_READAHEAD.value]}')
                    continue

                analysis.statistics.increment(Statistics.Key.PARSING_HITS)

                # ignore any dependency substring from the config ignore list
                dependency = getattr(parsing_result, CoreParsingKeyword.IMPORT_ENTITY_NAME.value)

                # try to resolve the dependency
                resolved_dependency = self.try_resolve_dependency(dependency, result, analysis)

                if self._is_dependency_in_ignore_list(resolved_dependency, analysis):
                    LOGGER.debug(f'ignoring dependency from {result.unique_name} to {resolved_dependency}')
                else:
                    result.scanned_import_dependencies.append(resolved_dependency)
                    LOGGER.debug(f'adding import: {resolved_dependency}')

    def try_resolve_dependency(self, dependency: str, result: AbstractFileResult, analysis) -> str:
        resolved_dependency = self.resolve_relative_dependency_path(dependency, str(result.absolute_dir_path), analysis.source_directory)
        check_dependency_path = f"{ Path(analysis.source_directory).parent}/{resolved_dependency}"
        if os.path.exists(check_dependency_path):
            dependency = resolved_dependency
        return dependency

    def _add_package_name_to_result(self, result: FileResult):
        result.module_name = ""


if __name__ == "__main__":
    LEXER = CParser()
    print(f'{LEXER.results=}')
