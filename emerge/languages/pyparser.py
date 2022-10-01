"""
Contains the implementation of the Python language parser and a relevant keyword enum.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict
from enum import Enum, unique

import logging
from pathlib import Path
import os

import coloredlogs
import pyparsing as pp

from emerge.languages.abstractparser import AbstractParser, ParsingMixin, Parser, CoreParsingKeyword, LanguageType
from emerge.results import FileResult
from emerge.abstractresult import AbstractResult, AbstractFileResult, AbstractEntityResult
from emerge.log import Logger
from emerge.stats import Statistics

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class PythonParsingKeyword(Enum):
    IMPORT = "import"
    FROM = "from"
    INLINE_COMMENT = "#"
    BLOCK_COMMENT = '"""'
    NEWLINE = '\n'
    EMPTY = ''
    BLANK = ' '
    PYTHON_IMPORT_PARENT_DIR = ".."
    PYTHON_IMPORT_CURRENT_DIR = "."
    PYTHON_UNIT_TEST_BRACKET = ">"
    RELATIVE_FROM_CURRENT_DIR = "from . "
    RELATIVE_FROM_PARENT_DIR = "from .. "
    PY_FILE_EXTENSION = ".py"


class PythonParser(AbstractParser, ParsingMixin):

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
        return Parser.PYTHON_PARSER.name

    @classmethod
    def language_type(cls) -> str:
        return LanguageType.PY.name

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
            scanned_language=LanguageType.PY,
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

    # pylint: disable=too-many-statements
    def _add_imports_to_result(self, result: AbstractFileResult, analysis):
        LOGGER.debug(f'extracting imports from file result {result.scanned_file_name}...')
        list_of_words_with_newline_strings = result.scanned_tokens

        source_string_no_comments = self._filter_source_tokens_without_comments(
            list_of_words_with_newline_strings,
            PythonParsingKeyword.INLINE_COMMENT.value,
            PythonParsingKeyword.BLOCK_COMMENT.value,
            PythonParsingKeyword.BLOCK_COMMENT.value
        )

        filtered_list_no_comments = self.preprocess_file_content_and_generate_token_list_by_mapping(source_string_no_comments, self._token_mappings)

        # for simplicity we can parse python dependencies just line by line
        source_import_lines = []
        line = PythonParsingKeyword.EMPTY.value
        for word in filtered_list_no_comments:
            if word is not PythonParsingKeyword.NEWLINE.value:
                line += word
                line += PythonParsingKeyword.BLANK.value  # make sure to seperate the words
            else:  # remove the last blank if NEWLINE is found
                line = line[:-1]
                # only append relevant lines with 'import'
                if line is not PythonParsingKeyword.EMPTY.value and PythonParsingKeyword.IMPORT.value in line \
                    and PythonParsingKeyword.PYTHON_UNIT_TEST_BRACKET.value not in line and line not in source_import_lines:
                    source_import_lines.append(line)
                line = PythonParsingKeyword.EMPTY.value

        # now iterate line by line are try to parse and resolve the dependencies
        for line in source_import_lines:

            relative_import = False
            global_import = True
            if PythonParsingKeyword.FROM.value in line:
                global_import = False

            expression_to_match = None
            multiple_imports_from_relative_current_dir = False
            multiple_imports_from_relative_parent_dir = False
            multiple_dependencies = []

            valid_name = pp.Word(
                pp.alphanums + \
                CoreParsingKeyword.DOT.value + \
                CoreParsingKeyword.UNDERSCORE.value + \
                CoreParsingKeyword.DASH.value + \
                CoreParsingKeyword.SLASH.value
            )

            valid_name_comma_seperated_imports = pp.Word(
                pp.alphanums + \
                CoreParsingKeyword.DOT.value + \
                CoreParsingKeyword.UNDERSCORE.value + \
                CoreParsingKeyword.DASH.value + \
                CoreParsingKeyword.SLASH.value + \
                CoreParsingKeyword.COMMA.value + " "
            )

            # case 'from . import <dependencies>'
            if PythonParsingKeyword.RELATIVE_FROM_CURRENT_DIR.value in line:
                multiple_imports_from_relative_current_dir = True
                expression_to_match = pp.Keyword(PythonParsingKeyword.FROM.value) + \
                    pp.Keyword(PythonParsingKeyword.PYTHON_IMPORT_CURRENT_DIR.value) + \
                    pp.Keyword(PythonParsingKeyword.IMPORT.value) + \
                    pp.OneOrMore(valid_name_comma_seperated_imports.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value))

            # case 'from .. import <dependencies>'
            elif PythonParsingKeyword.RELATIVE_FROM_PARENT_DIR.value in line:
                multiple_imports_from_relative_parent_dir = True
                expression_to_match = pp.Keyword(PythonParsingKeyword.FROM.value) + \
                    pp.Keyword(PythonParsingKeyword.PYTHON_IMPORT_PARENT_DIR.value) + \
                    pp.Keyword(PythonParsingKeyword.IMPORT.value) + \
                    pp.OneOrMore(valid_name_comma_seperated_imports.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value))

            # all other cases e.g. 'import <dependency>' or 'from foo.bar import <dependency>
            else:
                expression_to_match = (pp.Keyword(PythonParsingKeyword.IMPORT.value) | pp.Keyword(PythonParsingKeyword.FROM.value)) + \
                    valid_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value) + \
                    pp.Optional(pp.FollowedBy(pp.Keyword(PythonParsingKeyword.IMPORT.value)))

            try:
                parsing_result = expression_to_match.parseString(line)

                # if there are multiple dependencies, throw them all in multiple_dependencies
                if (multiple_imports_from_relative_current_dir or multiple_imports_from_relative_parent_dir) \
                    and CoreParsingKeyword.COMMA.value in getattr(parsing_result, CoreParsingKeyword.IMPORT_ENTITY_NAME.value):
                    multiple_results = getattr(parsing_result, CoreParsingKeyword.IMPORT_ENTITY_NAME.value)
                    multiple_dependencies = multiple_results.split(',')
                    multiple_dependencies = [s.strip() for s in multiple_dependencies]
                else:
                    multiple_imports_from_relative_current_dir = False
                    multiple_imports_from_relative_parent_dir = False

            except pp.ParseException as exception:
                result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
                LOGGER.warning(f'warning: could not parse result {result=}\n{exception}')
                continue

            analysis.statistics.increment(Statistics.Key.PARSING_HITS)

            # ignore any dependency substring from the config ignore list
            dependency = getattr(parsing_result, CoreParsingKeyword.IMPORT_ENTITY_NAME.value)

            # now try to resolve the dependency

            # case: 'from .. import dependency1, ..., dependencyN
            if multiple_imports_from_relative_parent_dir and not multiple_imports_from_relative_current_dir:
                for dep in multiple_dependencies:
                    resolved_dep = dep.replace(PythonParsingKeyword.PYTHON_IMPORT_PARENT_DIR.value, CoreParsingKeyword.POSIX_PARENT_DIRECTORY.value)

                    if f'{PythonParsingKeyword.PY_FILE_EXTENSION.value}' not in resolved_dep:
                        resolved_dep = f'{resolved_dep}{PythonParsingKeyword.PY_FILE_EXTENSION.value}'
                    if self._is_dependency_in_ignore_list(resolved_dep, analysis):
                        LOGGER.debug(f'ignoring dependency from {result.unique_name} to {resolved_dep}')
                    else:
                        result.scanned_import_dependencies.append(resolved_dep)
                        LOGGER.debug(f'adding import: {resolved_dep}')

            # case: 'from . import dependency1, ..., dependencyN
            elif multiple_imports_from_relative_current_dir and not multiple_imports_from_relative_parent_dir:
                for dep in multiple_dependencies:
                    resolved_dep = self.create_relative_analysis_path_for_dependency(dep, str(result.relative_analysis_path))

                    if f'{PythonParsingKeyword.PY_FILE_EXTENSION.value}' not in resolved_dep:
                        resolved_dep = f'{resolved_dep}{PythonParsingKeyword.PY_FILE_EXTENSION.value}'
                    if self._is_dependency_in_ignore_list(resolved_dep, analysis):
                        LOGGER.debug(f'ignoring dependency from {result.unique_name} to {resolved_dep}')
                    else:
                        result.scanned_import_dependencies.append(resolved_dep)
                        LOGGER.debug(f'adding import: {resolved_dep}')

            # all other cases
            elif not multiple_imports_from_relative_current_dir and not multiple_imports_from_relative_parent_dir:
                if PythonParsingKeyword.PYTHON_IMPORT_PARENT_DIR.value in dependency:
                    relative_import = True
                    dependency = dependency.replace(PythonParsingKeyword.PYTHON_IMPORT_PARENT_DIR.value, CoreParsingKeyword.POSIX_PARENT_DIRECTORY.value)

                if len(dependency) > 1 and CoreParsingKeyword.DOT.value == dependency[0] and CoreParsingKeyword.DOT.value is not dependency[1]:
                    relative_import = True
                    dependency = dependency[1:]

                if not global_import and relative_import and CoreParsingKeyword.POSIX_PARENT_DIRECTORY.value not in dependency:
                    dependency = self.create_relative_analysis_path_for_dependency(dependency, str(result.relative_analysis_path))
                elif not global_import and CoreParsingKeyword.POSIX_PARENT_DIRECTORY.value not in dependency:
                    posix_dependency = dependency.replace(CoreParsingKeyword.DOT.value, CoreParsingKeyword.SLASH.value)

                    if analysis.source_directory == CoreParsingKeyword.DOT.value:
                        relative_path = posix_dependency
                    else:
                        relative_path = f'{Path(analysis.source_directory).name}/{posix_dependency}'

                    check_dependency_path = f"{ Path(analysis.source_directory).parent}/{relative_path}"
                    if os.path.exists(f'{check_dependency_path}{PythonParsingKeyword.PY_FILE_EXTENSION.value}'):
                        dependency = f'{relative_path}{PythonParsingKeyword.PY_FILE_EXTENSION.value}'
                    else:
                        dependency = relative_path

                    if self._is_dependency_in_ignore_list(dependency, analysis):
                        LOGGER.debug(f'ignoring dependency from {result.unique_name} to {dependency}')
                    else:
                        result.scanned_import_dependencies.append(dependency)
                        LOGGER.debug(f'adding import: {dependency}')
                    continue

                if CoreParsingKeyword.POSIX_PARENT_DIRECTORY.value in dependency:  # contains at least one relative parent element '../'
                    dependency = self.resolve_relative_dependency_path(dependency, str(result.absolute_dir_path), analysis.source_directory)

                if not global_import:
                    dependency = dependency.replace(CoreParsingKeyword.DOT.value, CoreParsingKeyword.SLASH.value)

                if f'{PythonParsingKeyword.PY_FILE_EXTENSION.value}' not in dependency and not global_import:
                    dependency = f'{dependency}{PythonParsingKeyword.PY_FILE_EXTENSION.value}'

                if self._is_dependency_in_ignore_list(dependency, analysis):
                    LOGGER.debug(f'ignoring dependency from {result.unique_name} to {dependency}')
                else:
                    result.scanned_import_dependencies.append(dependency)
                    LOGGER.debug(f'adding import: {dependency}')

    def _add_package_name_to_result(self, result: FileResult):
        result.module_name = ""


if __name__ == "__main__":
    LEXER = PythonParser()
    print(f'{LEXER.results=}')
