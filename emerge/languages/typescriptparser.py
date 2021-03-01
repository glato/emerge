"""
Contains the implementation of the TypeScript language parser and a relevant keyword enum. This is basically a copy of the JavaScript parser with some nice modifications.
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

from emerge.languages.abstractparser import AbstractParser, AbstractParsingCore, Parser, CoreParsingKeyword, LanguageType
from emerge.results import FileResult
from emerge.abstractresult import AbstractResult, AbstractEntityResult
from emerge.statistics import Statistics
from emerge.logging import Logger

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class TypeScriptParsingKeyword(Enum):
    IMPORT = "import"
    FROM = "from"
    REQUIRE = "require"
    OPEN_SCOPE = "{"
    CLOSE_SCOPE = "}"
    INLINE_COMMENT = "//"
    START_BLOCK_COMMENT = "/*"
    STOP_BLOCK_COMMENT = "*/"


class TypeScriptParser(AbstractParser, AbstractParsingCore):

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
        return Parser.TYPESCRIPT_PARSER.name

    @property
    def results(self) -> Dict[str, AbstractResult]:
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    def generate_file_result_from_analysis(self, analysis, *, file_name: str, full_file_path: str, file_content: str) -> None:
        LOGGER.debug(f'generating file results...')
        scanned_tokens = self.preprocess_file_content_and_generate_token_list(file_content)

        # get relative path name starting from the anaylsis scanning path
        relative_project_path_name = full_file_path
        split_project_path = full_file_path.split(f"{analysis.source_directory}/")
        if len(split_project_path) > 1:
            relative_project_path_name = split_project_path[1]

        file_result = FileResult.create_file_result(
            analysis=analysis,
            scanned_file_name=file_name,
            absolute_name=full_file_path,
            display_name=file_name,
            module_name="",
            scanned_by=self.parser_name(),
            scanned_language=LanguageType.TYPESCRIPT,
            scanned_tokens=scanned_tokens
        )

        # use the relative full project path name as uniqe name of the result
        file_result.unique_name = relative_project_path_name

        self._add_package_name_to_result(file_result)
        self._add_imports_to_result(file_result, analysis)
        self._results[file_result.unique_name] = file_result

    def after_generated_file_results(self, analysis) -> None:
        pass

    def create_unique_entity_name(self, entity: AbstractEntityResult) -> None:
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def generate_entity_results_from_analysis(self, analysis):
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def _add_imports_to_result(self, result: AbstractResult, analysis):
        LOGGER.debug(f'extracting imports from base result {result.scanned_file_name}...')
        list_of_words_with_newline_strings = result.scanned_tokens
        source_string_no_comments = self._filter_source_tokens_without_comments(
            list_of_words_with_newline_strings, TypeScriptParsingKeyword.INLINE_COMMENT.value, TypeScriptParsingKeyword.START_BLOCK_COMMENT.value, TypeScriptParsingKeyword.STOP_BLOCK_COMMENT.value)
        filtered_list_no_comments = self.preprocess_file_content_and_generate_token_list_by_mapping(source_string_no_comments, self._token_mappings)

        for _, obj, following in self._gen_word_read_ahead(filtered_list_no_comments):
            if obj != TypeScriptParsingKeyword.IMPORT.value and obj != TypeScriptParsingKeyword.REQUIRE.value:
                continue

            read_ahead_string = self.create_read_ahead_string(obj, following)

            # grammar syntax for pyparsing to parse dependencies
            valid_name = pp.Word(pp.alphanums + CoreParsingKeyword.AT.value + CoreParsingKeyword.DOT.value + CoreParsingKeyword.ASTERISK.value +
                                    CoreParsingKeyword.UNDERSCORE.value + CoreParsingKeyword.DASH.value + CoreParsingKeyword.SLASH.value)

            if obj == TypeScriptParsingKeyword.IMPORT.value:
                expression_to_match = pp.SkipTo(pp.Literal(TypeScriptParsingKeyword.FROM.value)) + pp.Literal(TypeScriptParsingKeyword.FROM.value) + \
                    pp.OneOrMore(pp.Suppress(pp.Literal(CoreParsingKeyword.SINGLE_QUOTE.value)) | pp.Suppress(pp.Literal(CoreParsingKeyword.DOUBLE_QUOTE.value))) + \
                    pp.FollowedBy(pp.OneOrMore(valid_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value)))
            elif obj == TypeScriptParsingKeyword.REQUIRE.value:
                expression_to_match = pp.SkipTo(pp.Literal(CoreParsingKeyword.OPENING_ROUND_BRACKET.value)) + \
                    pp.Literal(CoreParsingKeyword.OPENING_ROUND_BRACKET.value) + \
                    pp.OneOrMore(pp.Suppress(pp.Literal(CoreParsingKeyword.SINGLE_QUOTE.value)) | pp.Suppress(pp.Literal(CoreParsingKeyword.DOUBLE_QUOTE.value))) + \
                    pp.FollowedBy(pp.OneOrMore(valid_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value)))

            try:
                # try to parse the dependency based on the syntax
                parsing_result = expression_to_match.parseString(read_ahead_string)
            except Exception as some_exception:
                result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
                LOGGER.warning(f'warning: could not parse result {result=}\n{some_exception}')
                LOGGER.warning(f'next tokens: {[obj] + following[:AbstractParsingCore.Constants.MAX_DEBUG_TOKENS_READAHEAD.value]}')
                continue

            analysis.statistics.increment(Statistics.Key.PARSING_HITS)

            dependency = getattr(parsing_result, CoreParsingKeyword.IMPORT_ENTITY_NAME.value)
            if CoreParsingKeyword.AT.value in dependency:
                pass  # let @-dependencies as they are
            elif dependency.count(CoreParsingKeyword.POSIX_CURRENT_DIRECTORY.value) == 1 and CoreParsingKeyword.POSIX_PARENT_DIRECTORY.value not in dependency:  # e.g. ./foo
                dependency = dependency.replace(CoreParsingKeyword.POSIX_CURRENT_DIRECTORY.value, '')
                if '.ts' not in dependency:
                    dependency = f"{dependency}.ts"
            elif CoreParsingKeyword.POSIX_PARENT_DIRECTORY.value in dependency:  # e.g. '../../foo.ts': a naive way to get a good/unique dependency path ...

                # ... first construct the result path + dependency path
                path = result.absolute_name.replace(os.path.basename(os.path.normpath(result.scanned_file_name)), "")
                path += dependency
                posix_path = PosixPath(path)
                try:
                    # then resolve the full path in a posix way
                    resolved_posix_path = posix_path.resolve()

                    project_scanning_path = analysis.source_directory
                    if project_scanning_path[-1] != CoreParsingKeyword.SLASH.value:
                        project_scanning_path = f"{project_scanning_path}{CoreParsingKeyword.SLASH.value}"

                    if project_scanning_path in str(resolved_posix_path):
                        # substract the beginning project source path
                        resolved_relative_path = str(resolved_posix_path).replace(f"{analysis.source_directory}{CoreParsingKeyword.SLASH.value}", "")
                        if '.ts' not in resolved_relative_path:
                            # assume the dependency is a ts file
                            resolved_relative_path = f"{resolved_relative_path}.ts"
                        # set our new constructed dependency
                        dependency = resolved_relative_path
                except:
                    pass

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
    LEXER = TypeScriptParser()
    print(f'{LEXER.results=}')
