"""
Contains the implementation of the Swift language parser and a relevant keyword enum.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, List
from enum import Enum, unique
import logging
from pathlib import Path

import pyparsing as pp
import coloredlogs

from emerge.languages.abstractparser import AbstractParser, ParsingMixin, Parser, CoreParsingKeyword, LanguageType
from emerge.results import FileResult, EntityResult
from emerge.abstractresult import AbstractResult, AbstractFileResult, AbstractEntityResult
from emerge.stats import Statistics
from emerge.log import Logger

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class SwiftParsingKeyword(Enum):
    CLASS = "class"
    STRUCT = "struct"
    PROTOCOL = "protocol"
    ENUM = "enum"
    VAR = "var"
    LET = "let"
    FUNC = "func"
    EXTENSION = "extension"
    OPEN_SCOPE = "{"
    CLOSE_SCOPE = "}"
    INLINE_COMMENT = "//"
    START_BLOCK_COMMENT = "/*"
    STOP_BLOCK_COMMENT = "*/"


class SwiftParser(AbstractParser, ParsingMixin):

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
            '"': ' " ',
            ".": ' . ',
        }

        # WORKAROUND: filter out entities that resulted from obvious parsing errors
        self._ignore_entity_keywords: List[str] = [
            'class', 'struct', 'protocol', 'enum', 'var', 'let', 'func', 'extension', 'import', 'fileprivate', 'value'
        ]

    @classmethod
    def parser_name(cls) -> str:
        return Parser.SWIFT_PARSER.name

    @classmethod
    def language_type(cls) -> str:
        return LanguageType.SWIFT.name

    @property
    def results(self) -> Dict[str, AbstractResult]:
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    def preprocess_swift_source(self, scanned_tokens) -> str:
        source_string_no_comments = self._filter_source_tokens_without_comments(
            scanned_tokens,
            SwiftParsingKeyword.INLINE_COMMENT.value,
            SwiftParsingKeyword.START_BLOCK_COMMENT.value,
            SwiftParsingKeyword.STOP_BLOCK_COMMENT.value
        )
        filtered_list_no_comments = self.preprocess_file_content_and_generate_token_list_by_mapping(source_string_no_comments, self._token_mappings)
        preprocessed_source_string = " ".join(filtered_list_no_comments)
        return preprocessed_source_string

    def generate_file_result_from_analysis(self, analysis, *, file_name: str, full_file_path: str, file_content: str) -> None:
        LOGGER.debug('generating file results...')

        #scanned_tokens: List[str] = self.preprocess_file_content_and_generate_token_list_by_mapping(file_content, self._token_mappings)
        scanned_tokens: List[str] = self.preprocess_file_content_and_generate_token_list(file_content)

        # make sure to create unique names by using the relative analysis path as a base for the result
        parent_analysis_source_path = f"{Path(analysis.source_directory).parent}/"
        relative_file_path_to_analysis = full_file_path.replace(parent_analysis_source_path, "")

        file_result = FileResult.create_file_result(
            analysis=analysis,
            scanned_file_name=relative_file_path_to_analysis,
            relative_file_path_to_analysis=relative_file_path_to_analysis,
            absolute_name=full_file_path,
            display_name=file_name,
            module_name="",
            scanned_by=self.parser_name(),
            scanned_language=LanguageType.SWIFT,
            scanned_tokens=scanned_tokens,
            preprocessed_source=""
        )

        self._add_package_name_to_result(file_result)
        self._results[file_result.unique_name] = file_result

    def after_generated_file_results(self, analysis) -> None:
        self._add_imports_to_file_results(analysis)

    def create_unique_entity_name(self, entity: AbstractEntityResult) -> None:
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def generate_entity_results_from_analysis(self, analysis):
        LOGGER.debug('generating entity results...')
        filtered_results: Dict[str, FileResult] = {k: v for (k, v) in self.results.items() \
            if v.analysis is analysis and isinstance(v, AbstractFileResult)}

        result: FileResult
        for _, result in filtered_results.items():

            entity_keywords: List[str] = [
                SwiftParsingKeyword.CLASS.value,
                SwiftParsingKeyword.STRUCT.value,
                SwiftParsingKeyword.ENUM.value,
                SwiftParsingKeyword.PROTOCOL.value
            ]

            entity_name = pp.Word(pp.alphanums + CoreParsingKeyword.DOT.value + CoreParsingKeyword.UNDERSCORE.value)

            match_expression = (
                pp.Keyword(SwiftParsingKeyword.CLASS.value) |
                pp.Keyword(SwiftParsingKeyword.STRUCT.value) |
                pp.Keyword(SwiftParsingKeyword.ENUM.value) |
                pp.Keyword(SwiftParsingKeyword.PROTOCOL.value)) + \
                (~pp.Keyword(SwiftParsingKeyword.LET.value) &
                 ~pp.Keyword(SwiftParsingKeyword.VAR.value) &
                 ~pp.Keyword(SwiftParsingKeyword.FUNC.value)) + \
                entity_name.setResultsName(CoreParsingKeyword.ENTITY_NAME.value) + \
                pp.Optional(pp.Keyword(CoreParsingKeyword.COLON.value)) + pp.SkipTo(pp.FollowedBy(SwiftParsingKeyword.OPEN_SCOPE.value))

            comment_keywords: Dict[str, str] = {
                CoreParsingKeyword.LINE_COMMENT.value: SwiftParsingKeyword.INLINE_COMMENT.value,
                CoreParsingKeyword.START_BLOCK_COMMENT.value: SwiftParsingKeyword.START_BLOCK_COMMENT.value,
                CoreParsingKeyword.STOP_BLOCK_COMMENT.value: SwiftParsingKeyword.STOP_BLOCK_COMMENT.value
            }

            entity_results_unfiltered = result.generate_entity_results_from_scopes(entity_keywords, match_expression, comment_keywords)
            entity_results: List[AbstractEntityResult] = []

            # WORKAROUND: filter out entities that resulted from obvious parsing errors
            filtered_entity_results = [x for x in entity_results_unfiltered if not x.entity_name in self._ignore_entity_keywords]

            # filter even more on the basis of a configured ignore list
            for entity_result in filtered_entity_results:
                if self.is_entity_in_ignore_list(entity_result.entity_name, analysis):
                    pass
                else:
                    entity_results.append(entity_result)

            for entity_result in entity_results:
                LOGGER.debug(f'{entity_result.entity_name=}')
                self._add_inheritance_to_entity_result(entity_result)
                self._results[entity_result.entity_name] = entity_result

        self._add_extensions_to_entity_results(analysis)
        self._add_imports_to_entity_results(analysis)

    def _add_extensions_to_entity_results(self, analysis) -> None:
        LOGGER.debug('adding swift extensions to entity results...')

        entity_results: Dict[str, EntityResult] = {
            k: v for (k, v) in self.results.items() if v.analysis is analysis and isinstance(v, EntityResult)
        }

        file_results: Dict[str, FileResult] = {
            k: v for (k, v) in self.results.items() if v.analysis is analysis and isinstance(v, FileResult)
        }

        entity_names: List[str] = [v.entity_name for _, v in entity_results.items()]

        result: FileResult
        for _, result in file_results.items():
            entity_keywords: List[str] = [SwiftParsingKeyword.EXTENSION.value]
            entity_name_of_extension = pp.Word(pp.alphanums)

            match_expression = pp.Keyword(SwiftParsingKeyword.EXTENSION.value) + \
                entity_name_of_extension.setResultsName(CoreParsingKeyword.ENTITY_NAME.value) + \
                     pp.SkipTo(pp.FollowedBy(SwiftParsingKeyword.OPEN_SCOPE.value))

            comment_keywords: Dict[str, str] = {CoreParsingKeyword.LINE_COMMENT.value: SwiftParsingKeyword.INLINE_COMMENT.value,
                                                CoreParsingKeyword.START_BLOCK_COMMENT.value: SwiftParsingKeyword.START_BLOCK_COMMENT.value,
                                                CoreParsingKeyword.STOP_BLOCK_COMMENT.value: SwiftParsingKeyword.STOP_BLOCK_COMMENT.value}

            extension_entity_results: List[EntityResult] = result.generate_entity_results_from_scopes(entity_keywords,
                                                                                                    match_expression,
                                                                                                    comment_keywords)

            for extension in extension_entity_results:
                if extension.entity_name in entity_names:
                    entity_result: AbstractEntityResult = analysis.result_by_entity_name(extension.entity_name, entity_results)
                    if entity_result is not None:
                        entity_result.scanned_tokens.extend(extension.scanned_tokens)
                        LOGGER.debug(f'added extension from file result {result=} to entity result: {entity_result=}.')

    def _add_imports_to_entity_results(self, analysis) -> None:
        LOGGER.debug('adding imports to entity result...')
        entity_results: Dict[str, AbstractEntityResult] = {
            k: v for (k, v) in self.results.items() if v.analysis is analysis and isinstance(v, AbstractEntityResult)
        }

        entity_names: List[str] = [v.entity_name for _, v in entity_results.items()]

        for _, result in entity_results.items():
            for token in result.scanned_tokens:
                if token in entity_names and token not in result.scanned_import_dependencies and \
                    (token.lower() != result.entity_name.lower()) and \
                    token not in result.scanned_inheritance_dependencies:

                    # ignore any dependency substring from the config ignore list
                    if self._is_dependency_in_ignore_list(token, analysis):
                        LOGGER.debug(f'ignoring dependency from {result.entity_name} to {token}')
                    else:
                        result.scanned_import_dependencies.append(token)

    def _add_imports_to_file_results(self, analysis) -> None:
        """Adds imports to file results. Since Swift has no direct include directives for files,
        we have to do a little workaround here:
        1. We extract all entities + entity names
        2. We loop though all entity results/ file results and check if an entity name is part of a file results scanned tokens.
        If this is the case we add an import dependency.

        Args:
            analysis (Analysis): A given analysis.
        """
        LOGGER.debug('adding imports to file results...')
        entity_results: Dict[str, EntityResult] = {}

        filtered_results: Dict[str, FileResult] = {k: v for (k, v) in self.results.items() if v.analysis is analysis and isinstance(v, FileResult)}

        # 1. extract entities
        result: FileResult
        for _, result in filtered_results.items():

            entity_keywords: List[str] = [
                SwiftParsingKeyword.CLASS.value,
                SwiftParsingKeyword.STRUCT.value,
                SwiftParsingKeyword.ENUM.value,
                SwiftParsingKeyword.PROTOCOL.value
            ]

            entity_name = pp.Word(pp.alphanums)

            match_expression = (pp.Keyword(SwiftParsingKeyword.CLASS.value) |
                                pp.Keyword(SwiftParsingKeyword.STRUCT.value) |
                                pp.Keyword(SwiftParsingKeyword.ENUM.value) |
                                pp.Keyword(SwiftParsingKeyword.PROTOCOL.value)) + \
                (~pp.Keyword(SwiftParsingKeyword.LET.value) & ~pp.Keyword(SwiftParsingKeyword.VAR.value) & ~pp.Keyword(SwiftParsingKeyword.FUNC.value)) + \
                entity_name.setResultsName(CoreParsingKeyword.ENTITY_NAME.value) + \
                pp.Optional(pp.Keyword(CoreParsingKeyword.COLON.value)) + pp.SkipTo(pp.FollowedBy(SwiftParsingKeyword.OPEN_SCOPE.value))

            comment_keywords: Dict[str, str] = {
                CoreParsingKeyword.LINE_COMMENT.value: SwiftParsingKeyword.INLINE_COMMENT.value,
                CoreParsingKeyword.START_BLOCK_COMMENT.value: SwiftParsingKeyword.START_BLOCK_COMMENT.value,
                CoreParsingKeyword.STOP_BLOCK_COMMENT.value: SwiftParsingKeyword.STOP_BLOCK_COMMENT.value
            }

            entity_results_extracted_from_file = result.generate_entity_results_from_scopes(entity_keywords, match_expression, comment_keywords)

            # TODO: also add tokens from extensions

            entity_result: AbstractEntityResult
            for entity_result in entity_results_extracted_from_file:
                LOGGER.debug(f'{entity_result.entity_name=}')
                self._add_inheritance_to_entity_result(entity_result)
                entity_results[entity_result.entity_name] = entity_result

        # 2. if entity names are present in scanned tokens of file results, add to import dependencies
        for name, entity_result in entity_results.items():
            for _, file_result in filtered_results.items():
                if name in file_result.scanned_tokens and entity_result.scanned_file_name not in file_result.scanned_import_dependencies:

                    # dependency = os.path.basename(os.path.normpath(entity_result.scanned_file_name))
                    dependency = entity_result.scanned_file_name

                    if self._is_dependency_in_ignore_list(dependency, analysis):
                        LOGGER.debug(f'ignoring dependency from {file_result.unique_name} to {dependency}')
                    else:
                        file_result.scanned_import_dependencies.append(dependency)
                        LOGGER.debug(f'adding import: {dependency}')

    def _add_package_name_to_result(self, result: FileResult):
        result.module_name = result.scanned_file_name
        LOGGER.debug(f'added filename as package prefix: {result.scanned_file_name} and added to result')

    def _add_inheritance_to_entity_result(self, result: AbstractEntityResult) -> None:
        LOGGER.debug(f'extracting inheritance from entity result {result.entity_name}...')
        for _, obj, following in self._gen_word_read_ahead(result.scanned_tokens):
            if obj == SwiftParsingKeyword.CLASS.value or \
               obj == SwiftParsingKeyword.STRUCT.value or \
               obj == SwiftParsingKeyword.ENUM.value or \
               obj == SwiftParsingKeyword.PROTOCOL.value:
                read_ahead_string = self.create_read_ahead_string(obj, following)

                entity_name = pp.Word(pp.alphanums + CoreParsingKeyword.DOT.value)
                expression_to_match = (pp.Keyword(SwiftParsingKeyword.CLASS.value) |
                                        pp.Keyword(SwiftParsingKeyword.STRUCT.value) |
                                        pp.Keyword(SwiftParsingKeyword.ENUM.value) |
                                        pp.Keyword(SwiftParsingKeyword.PROTOCOL.value) ) + \
                                        entity_name.setResultsName(CoreParsingKeyword.ENTITY_NAME.value) + \
                                        pp.Keyword(CoreParsingKeyword.COLON.value) + \
                    entity_name.setResultsName(CoreParsingKeyword.INHERITED_ENTITY_NAME.value) + \
                         pp.SkipTo(pp.FollowedBy(SwiftParsingKeyword.OPEN_SCOPE.value))

                try:
                    parsing_result = expression_to_match.parseString(read_ahead_string)
                # pylint: disable=bare-except
                except:
                    result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
                    LOGGER.warning(f'warning: could not parse result {result=}')
                    LOGGER.warning(f'next tokens: {[obj] + following[:ParsingMixin.Constants.MAX_DEBUG_TOKENS_READAHEAD.value]}')
                    continue

                if len(parsing_result) > 0:
                    parsing_result = expression_to_match.parseString(read_ahead_string)

                    if getattr(parsing_result, CoreParsingKeyword.INHERITED_ENTITY_NAME.value) is not None and \
                       bool(getattr(parsing_result, CoreParsingKeyword.INHERITED_ENTITY_NAME.value)):

                        result.analysis.statistics.increment(Statistics.Key.PARSING_HITS)
                        LOGGER.debug(
                            f'found inheritance class {getattr(parsing_result, CoreParsingKeyword.INHERITED_ENTITY_NAME.value)}' + \
                            'for entity name: {getattr(parsing_result, CoreParsingKeyword.ENTITY_NAME.value)} and added to result')
                        result.scanned_inheritance_dependencies.append(getattr(parsing_result, CoreParsingKeyword.INHERITED_ENTITY_NAME.value))


if __name__ == "__main__":
    LEXER = SwiftParser()
    print(f'{LEXER.results=}')
