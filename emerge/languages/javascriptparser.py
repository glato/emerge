"""
Contains the implementation of the JavaScript language parser and a relevant keyword enum.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import pyparsing as pp
from typing import Dict
from enum import Enum, unique
import coloredlogs
import logging
from pathlib import PosixPath
import os

from emerge.languages.abstractparser import AbstractParser, ParsingMixin, Parser, CoreParsingKeyword, LanguageType
from emerge.results import FileResult
from emerge.abstractresult import AbstractFileResult, AbstractResult, AbstractEntityResult
from emerge.statistics import Statistics
from emerge.logging import Logger

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class JavaScriptParsingKeyword(Enum):
    IMPORT = "import"
    FROM = "from"
    REQUIRE = "require"
    OPEN_SCOPE = "{"
    CLOSE_SCOPE = "}"
    INLINE_COMMENT = "//"
    START_BLOCK_COMMENT = "/*"
    STOP_BLOCK_COMMENT = "*/"


class JavaScriptParser(AbstractParser, ParsingMixin):

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
            "'": " ' "
        }

    @classmethod
    def parser_name(cls) -> str:
        return Parser.JAVASCRIPT_PARSER.name

    @property
    def results(self) -> Dict[str, AbstractResult]:
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    def generate_file_result_from_analysis(self, analysis, *, file_name: str, full_file_path: str, file_content: str) -> None:
        LOGGER.debug(f'generating file results...')
        scanned_tokens = self.preprocess_file_content_and_generate_token_list(file_content)

        # make sure to create unique names by using the relative analysis path as a base for the result
        relative_file_path_to_analysis = self.create_relative_analysis_file_path(analysis.source_directory, full_file_path)

        file_result = FileResult.create_file_result(
            analysis=analysis,
            scanned_file_name=file_name,
            relative_file_path_to_analysis=relative_file_path_to_analysis,
            absolute_name=full_file_path,
            display_name=relative_file_path_to_analysis,
            module_name="",
            scanned_by=self.parser_name(),
            scanned_language=LanguageType.JAVASCRIPT,
            scanned_tokens=scanned_tokens
        )

        self._add_package_name_to_result(file_result)
        self._add_imports_to_file_result(file_result, analysis)
        self._results[file_result.unique_name] = file_result

    def after_generated_file_results(self, analysis) -> None:
        pass

    def create_unique_entity_name(self, entity: AbstractEntityResult) -> None:
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def generate_entity_results_from_analysis(self, analysis):
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def _add_imports_to_file_result(self, result: AbstractFileResult, analysis):
        LOGGER.debug(f'extracting imports from base result {result.scanned_file_name}...')

        # prepare list of tokens
        list_of_words_with_newline_strings = result.scanned_tokens
        source_string_no_comments = self._filter_source_tokens_without_comments(
            list_of_words_with_newline_strings, JavaScriptParsingKeyword.INLINE_COMMENT.value, JavaScriptParsingKeyword.START_BLOCK_COMMENT.value, JavaScriptParsingKeyword.STOP_BLOCK_COMMENT.value)
        filtered_list_no_comments = self.preprocess_file_content_and_generate_token_list_by_mapping(source_string_no_comments, self._token_mappings)

        for _, obj, following in self._gen_word_read_ahead(filtered_list_no_comments):
            if obj != JavaScriptParsingKeyword.IMPORT.value and obj != JavaScriptParsingKeyword.REQUIRE.value:
                continue

            read_ahead_string = self.create_read_ahead_string(obj, following)

            # create parsing expression
            valid_name = pp.Word(pp.alphanums + CoreParsingKeyword.AT.value + CoreParsingKeyword.DOT.value + CoreParsingKeyword.ASTERISK.value +
                                 CoreParsingKeyword.UNDERSCORE.value + CoreParsingKeyword.DASH.value + CoreParsingKeyword.SLASH.value)

            if obj == JavaScriptParsingKeyword.IMPORT.value:
                expression_to_match = pp.SkipTo(pp.Literal(JavaScriptParsingKeyword.FROM.value)) + pp.Literal(JavaScriptParsingKeyword.FROM.value) + \
                    pp.OneOrMore(pp.Suppress(pp.Literal(CoreParsingKeyword.SINGLE_QUOTE.value)) | pp.Suppress(pp.Literal(CoreParsingKeyword.DOUBLE_QUOTE.value))) + \
                    pp.FollowedBy(pp.OneOrMore(valid_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value)))
            elif obj == JavaScriptParsingKeyword.REQUIRE.value:
                expression_to_match = pp.SkipTo(pp.Literal(CoreParsingKeyword.OPENING_ROUND_BRACKET.value)) + \
                    pp.Literal(CoreParsingKeyword.OPENING_ROUND_BRACKET.value) + \
                    pp.OneOrMore(pp.Suppress(pp.Literal(CoreParsingKeyword.SINGLE_QUOTE.value)) | pp.Suppress(pp.Literal(CoreParsingKeyword.DOUBLE_QUOTE.value))) + \
                    pp.FollowedBy(pp.OneOrMore(valid_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value)))

            try:
                # parse the dependency based on the expression
                parsing_result = expression_to_match.parseString(read_ahead_string)
            except Exception as some_exception:
                result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
                LOGGER.warning(f'warning: could not parse result {result=}\n{some_exception}')
                LOGGER.warning(f'next tokens: {[obj] + following[:ParsingMixin.Constants.MAX_DEBUG_TOKENS_READAHEAD.value]}')
                continue

            analysis.statistics.increment(Statistics.Key.PARSING_HITS)

            # now try to resolve/adjust the dependency to have a unique path
            dependency = getattr(parsing_result, CoreParsingKeyword.IMPORT_ENTITY_NAME.value)

            if CoreParsingKeyword.AT.value in dependency:
                pass  # let @-dependencies as they are

            # check for index.js imports (https://nodejs.org/api/modules.html#modules_all_together)
            elif dependency == CoreParsingKeyword.DOT.value:
                index_dependency = dependency.replace(CoreParsingKeyword.DOT.value, './index.js')
                index_dependency = self.resolve_relative_dependency_path(index_dependency, result.absolute_dir_path, analysis.source_directory)
                check_dependency_path = f"{ PosixPath(analysis.source_directory).parent}/{index_dependency}"
                if os.path.exists(check_dependency_path):  # check if the resolved index_dependency exists, then modify
                    dependency = f"{index_dependency}"

            elif dependency.count(CoreParsingKeyword.POSIX_CURRENT_DIRECTORY.value) == 1 and CoreParsingKeyword.POSIX_PARENT_DIRECTORY.value not in dependency:  # e.g. ./foo
                dependency = dependency.replace(CoreParsingKeyword.POSIX_CURRENT_DIRECTORY.value, '')
                dependency = self.create_relative_analysis_path_for_dependency(dependency, result.relative_analysis_path)  # adjust dependency to have a relative analysis path

            elif CoreParsingKeyword.POSIX_PARENT_DIRECTORY.value in dependency:  # contains at lease one relative parent element '../'
                dependency = self.resolve_relative_dependency_path(dependency, result.absolute_dir_path, analysis.source_directory)

            # check and verify if we need to add a remaining .js suffix
            check_dependency_path = f"{ PosixPath(analysis.source_directory).parent}/{dependency}.js"
            if PosixPath(dependency).suffix is not ".js" and os.path.exists(check_dependency_path):
                dependency = f"{dependency}.js"

            # ignore any dependency substring from the config ignore list
            if self._is_dependency_in_ignore_list(dependency, analysis):
                LOGGER.debug(f'ignoring dependency from {result.unique_name} to {dependency}')
            else:
                result.scanned_import_dependencies.append(dependency)
                LOGGER.debug(f'adding import: {dependency} to {result.unique_name}')

    # pylint: disable=unused-argument
    def _add_package_name_to_result(self, result: AbstractResult) -> str:
        LOGGER.warning(f'currently not supported in {self.parser_name}')

    # pylint: disable=unused-argument
    def _add_inheritance_to_entity_result(self, result: AbstractEntityResult):
        LOGGER.warning(f'currently not supported in {self.parser_name}')


if __name__ == "__main__":
    LEXER = JavaScriptParser()
    print(f'{LEXER.results=}')
