"""
Contains the implementation of the Ruby language parser and a relevant keyword enum.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import pyparsing as pp
from typing import Dict
from enum import Enum, unique
import coloredlogs
import logging
from emerge.languages.abstractparser import AbstractParser, AbstractParsingCore, Parser, CoreParsingKeyword, LanguageType
from emerge.results import FileResult
from emerge.abstractresult import AbstractResult, AbstractEntityResult
from emerge.statistics import Statistics
from emerge.logging import Logger

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class RubyParsingKeyword(Enum):
    CLASS = "class"
    CLOSE_SCOPE = "end"
    INLINE_COMMENT = "#"
    START_BLOCK_COMMENT = "=begin"
    STOP_BLOCK_COMMENT = "=end"
    REQUIRE = "require"


class RubyParser(AbstractParser, AbstractParsingCore):

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
        return Parser.RUBY_PARSER.name

    @property
    def results(self) -> Dict[str, AbstractResult]:
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    def generate_file_result_from_analysis(self, analysis, *, file_name: str, full_file_path: str, file_content: str) -> None:
        LOGGER.debug(f'generating file results...')
        scanned_tokens = self.preprocess_file_content_and_generate_token_list(file_content)

        file_result = FileResult.create_file_result(
            analysis=analysis,
            scanned_file_name=file_name,
            internal_name=full_file_path,
            module_name="",
            scanned_by=self.parser_name(),
            scanned_language=LanguageType.RUBY,
            scanned_tokens=scanned_tokens
        )

        self._add_imports_to_result(file_result, analysis)
        self._results[file_result.unique_name] = file_result

    def after_generated_file_results(self, analysis) -> None:
        pass

    def create_unique_entity_name(self, *, entity: AbstractEntityResult) -> None:
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def generate_entity_results_from_analysis(self, analysis):
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def _add_imports_to_result(self, result: AbstractResult, analysis):
        LOGGER.debug(f'extracting imports from file result {result.scanned_file_name}...')
        list_of_words_with_newline_strings = result.scanned_tokens
        source_string_no_comments = self._filter_source_tokens_without_comments(
            list_of_words_with_newline_strings, RubyParsingKeyword.INLINE_COMMENT.value, RubyParsingKeyword.START_BLOCK_COMMENT.value, RubyParsingKeyword.STOP_BLOCK_COMMENT.value)
        filtered_list_no_comments = self.preprocess_file_content_and_generate_token_list_by_mapping(source_string_no_comments, self._token_mappings)

        for _, obj, following in self._gen_word_read_ahead(filtered_list_no_comments):
            if obj == RubyParsingKeyword.REQUIRE.value:
                read_ahead_string = self.create_read_ahead_string(obj, following)

                import_name = pp.Word(pp.alphanums + CoreParsingKeyword.UNDERSCORE.value + CoreParsingKeyword.SLASH.value + CoreParsingKeyword.DOT.value)
                ignore_between_require_and_import_name = pp.Word(pp.alphanums + CoreParsingKeyword.UNDERSCORE.value +
                                                                 CoreParsingKeyword.DOT.value + CoreParsingKeyword.OPENING_ROUND_BRACKET.value)

                expression_to_match = pp.Keyword(RubyParsingKeyword.REQUIRE.value) + (

                    (pp.Keyword(CoreParsingKeyword.SINGLE_QUOTE.value) +
                     import_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value) +
                     pp.Keyword(CoreParsingKeyword.SINGLE_QUOTE.value)) |

                    (pp.Keyword(CoreParsingKeyword.DOUBLE_QUOTE.value) +
                     import_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value) +
                     pp.Keyword(CoreParsingKeyword.DOUBLE_QUOTE.value)) |

                    pp.OneOrMore(ignore_between_require_and_import_name) + pp.Suppress(pp.Keyword(CoreParsingKeyword.SINGLE_QUOTE.value) | pp.Keyword(CoreParsingKeyword.DOUBLE_QUOTE.value)) +
                    import_name.setResultsName(CoreParsingKeyword.IMPORT_ENTITY_NAME.value)

                )

                try:
                    parsing_result = expression_to_match.parseString(read_ahead_string)
                except Exception as some_exception:
                    result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
                    LOGGER.warning(f'warning: could not parse result {result=}\n{some_exception}')
                    LOGGER.warning(f'next tokens: {[obj] + following[:AbstractParsingCore.Constants.MAX_DEBUG_TOKENS_READAHEAD.value]}')
                    continue

                analysis.statistics.increment(Statistics.Key.PARSING_HITS)

                # ignore any dependency substring from the config ignore list
                dependency = getattr(parsing_result, CoreParsingKeyword.IMPORT_ENTITY_NAME.value)
                if self._is_dependency_in_ignore_list(dependency, analysis):
                    LOGGER.debug(f'ignoring dependency from {result.unique_name} to {dependency}')
                else:
                    result.scanned_import_dependencies.append(dependency)
                    LOGGER.debug(f'adding import: {dependency}')


if __name__ == "__main__":
    LEXER = RubyParser()
    print(f'{LEXER.results=}')
