"""
Contains the implementation of the Go language parser and a relevant keyword enum.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, List, Any
from enum import Enum, unique
import logging
import re
from pathlib import Path

import pyparsing as pp

import coloredlogs
from emerge.graph import GraphType

from emerge.languages.abstractparser import AbstractParser, ParsingMixin, Parser, CoreParsingKeyword, LanguageType
from emerge.results import FileResult
from emerge.abstractresult import AbstractFileResult, AbstractEntityResult
from emerge.log import Logger
from emerge.stats import Statistics

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)

@unique
class GoParsingKeyword(Enum):
    IMPORT = "import"
    INLINE_COMMENT = "//"
    START_BLOCK_COMMENT = "/*"
    STOP_BLOCK_COMMENT = "*/"


class GoParser(AbstractParser, ParsingMixin):

    def __init__(self):
        self._results: Dict[str, AbstractFileResult] = {}
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
            '&': ' & ',
            '...': ' ... ',
        }
        self.dependencies_grammar = self.create_golang_dependencies_grammar()
        self.compiled_func_grammar = self.compile_golang_func_grammar_with_re()
        self.compiled_struct_grammar = self.compile_golang_struct_grammar_with_re()

    @classmethod
    def parser_name(cls) -> str:
        return Parser.GO_PARSER.name

    @classmethod
    def language_type(cls) -> str:
        return LanguageType.GO.name

    @property
    def results(self) -> Dict[str, Any]:
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    def preprocess_golang_source(self, scanned_tokens) -> str:
        source_string_no_comments = self._filter_source_tokens_without_comments(
            scanned_tokens,
            GoParsingKeyword.INLINE_COMMENT.value,
            GoParsingKeyword.START_BLOCK_COMMENT.value,
            GoParsingKeyword.STOP_BLOCK_COMMENT.value
        )
        filtered_list_no_comments = self.preprocess_file_content_and_generate_token_list_by_mapping(source_string_no_comments, self._token_mappings)
        preprocessed_source_string = " ".join(filtered_list_no_comments)
        return preprocessed_source_string

    def generate_file_result_from_analysis(self, analysis, *, file_name: str, full_file_path: str, file_content: str) -> None:
        LOGGER.debug('generating file results...')
        scanned_tokens = self.preprocess_file_content_and_generate_token_list_by_mapping(file_content, self._token_mappings)

        # make sure to create unique names by using the relative analysis path as a base for the result
        parent_analysis_source_path = f"{Path(analysis.source_directory).parent}/"
        relative_file_path_to_analysis = full_file_path.replace(parent_analysis_source_path, "")
        preprocessed_source = self.preprocess_golang_source(scanned_tokens)

        file_result = FileResult.create_file_result(
            analysis=analysis,
            scanned_file_name=file_name,
            relative_file_path_to_analysis=relative_file_path_to_analysis,
            absolute_name=full_file_path,
            display_name=file_name,
            module_name="",
            scanned_by=self.parser_name(),
            scanned_language=LanguageType.GO,
            scanned_tokens=scanned_tokens,
            preprocessed_source=preprocessed_source
        )

        self._add_package_name_to_result(file_result)
        self._results[file_result.unique_name] = file_result

    def after_generated_file_results(self, analysis) -> None:
        file_result: AbstractFileResult
        for _, file_result in self._results.items():
            self._add_imports_to_result(file_result, analysis)

    def generate_entity_results_from_analysis(self, analysis):
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def create_unique_entity_name(self, entity: AbstractEntityResult) -> None:
        raise NotImplementedError(f'currently not implemented in {self.parser_name()}')

    def parse_grammar(self, analysis, grammar, preprocessed_source_string: str) -> List[str]:
        try:
            # searchString: skim through the input looking for matches, instead of requiring a complete match of all the content in the input string
            parsing_result = grammar.searchString(preprocessed_source_string)
        except pp.ParseException as exception:
            analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
            LOGGER.warning(f'warning: could not parse result: {exception}')
            return []
            
        list_parsing_result = parsing_result.asList()
        list_parsing_result = [item for sublist in list_parsing_result for item in sublist] # flatten list

        return list_parsing_result

    # e.g. "type encbuf struct {"
    # method is readably but unfortunately very slow
    @staticmethod
    def create_golang_struct_grammar():
        # pylint: disable=invalid-name
        STRUCT_NAME = pp.Word(pp.alphanums + '_')
        STRUCT_LINE = pp.Suppress(pp.Keyword('type')) + STRUCT_NAME + pp.Suppress(pp.Keyword('struct'))
        grammar = STRUCT_LINE
        # pylint: enable=invalid-name
        return grammar

    # e.g. "func DefaultTenantConfigs() *TenantConfigs {" or "func (o *TenantConfigs) LogPushRequest(userID string) bool {"
    # method is readably but unfortunately very slow
    @staticmethod
    def create_golang_func_grammar():
        # pylint: disable=invalid-name
        FUNC_NAME = pp.Word(pp.alphanums + '_')
        PARAMETER_DEF = pp.Word(pp.alphanums + '_' + '*' + '.' + ',' )
        FUNC_LINE = pp.Suppress(pp.Keyword('func')) + pp.Optional( pp.Suppress( pp.Keyword('(') + pp.ZeroOrMore(PARAMETER_DEF) + pp.Keyword(')')) ) + FUNC_NAME
        grammar = FUNC_LINE
        # pylint: enable=invalid-name
        return grammar

    @staticmethod
    def compile_golang_func_grammar_with_re():
        pattern = r"func\s(?:\(\s*\w*\s*\**\w*\s*\)\s*)?(?P<fname>\w*)?"
        return re.compile(pattern)

    @staticmethod
    def compile_golang_struct_grammar_with_re():
        pattern = r"type\s(\w*)?\s*struct"
        return re.compile(pattern)

    @staticmethod
    def create_golang_dependencies_grammar():
        # pylint: disable=invalid-name
        IMPORT_NAME = pp.Word(pp.alphanums + CoreParsingKeyword.DOT.value + CoreParsingKeyword.ASTERISK.value +
                            CoreParsingKeyword.UNDERSCORE.value + CoreParsingKeyword.DASH.value + CoreParsingKeyword.SLASH.value)
        IMPORT_ALIAS = IMPORT_NAME

        NL = pp.Suppress(pp.LineEnd())
        MULTILINE = pp.Suppress(pp.Optional(IMPORT_ALIAS)) + \
                pp.Suppress(pp.Keyword('"')) + pp.OneOrMore(IMPORT_NAME) + pp.Suppress(pp.Keyword('"')) + NL | NL
        MULTILINES = pp.OneOrMore(pp.Group(MULTILINE))

        grammar = (
            (   # a) multiline go import
                pp.Suppress( pp.Literal(GoParsingKeyword.IMPORT.value) + pp.Keyword('(')) + MULTILINES + pp.Suppress(pp.Keyword(')'))
            ) | 
            (   # b) single line go import
                pp.Suppress( pp.Literal(GoParsingKeyword.IMPORT.value)) + MULTILINE
            )
        )
        # pylint: enable=invalid-name
        return grammar

    def _add_imports_to_result(self, result: AbstractFileResult, analysis):
        LOGGER.debug(f'extracting imports from file result {result.scanned_file_name}...')

        filesystem_graph = analysis.graph_representations[GraphType.FILESYSTEM_GRAPH.name.lower()]
        extracted_dependencies = self.parse_grammar(analysis, self.dependencies_grammar, result.preprocessed_source)

        for parsed_dependency in extracted_dependencies:
            analysis.statistics.increment(Statistics.Key.PARSING_HITS)

            # consider dependency a pure string, if we get a string result from b) single line go import
            if isinstance(parsed_dependency, str):
                dependency = parsed_dependency
            else: # otherwise if we get a list of ParseResults, use the string name of the dependency
                dependency = parsed_dependency[0]

            if self._is_dependency_in_ignore_list(dependency, analysis):
                LOGGER.debug(f'ignoring dependency from {result.unique_name} to {dependency}')
            else:
                dependency_is_resolved = False
                if '/' in dependency:
                    
                    # we already have hashed all scanned dependency paths, if the new dependency was already
                    # scanned before and we can resolve it by checking if it fits at the end of the new dependency
                    for scanned_dependency in analysis.absolute_scanned_file_names:
                        check_for_scanned_dependency = scanned_dependency.replace('.go', '')
                        if dependency.endswith(check_for_scanned_dependency):
                            dependency = f'{check_for_scanned_dependency}.go'
                            dependency_is_resolved = True

                    # otherwise we have to try resolving a package dependency based on our constructed file graph
                    # where a package may use symbols from all golang source files only in the imported target directory
                    # the approach here is: check if any important symbols (e.g. methods, structs) from each source file
                    # in the given directory is used in the new dependency. if so, add to its imported dependencies.
                    if dependency_is_resolved is False:
                        some_nodes = filesystem_graph.digraph.nodes

                        for node_name, filesystem_node in some_nodes.items():
                            if filesystem_node['directory'] is False:
                                continue

                            if dependency.endswith(node_name):

                                file_nodes_from_dir_node = []
                                if node_name in analysis.scanned_files_nodes_in_directories:
                                    file_nodes_from_dir_node = analysis.scanned_files_nodes_in_directories[node_name]
                                
                                # get all possible source files that might be an import candidate
                                potential_imported_results = []
                                for filesystem_result in file_nodes_from_dir_node:
                                    results: Dict[str, AbstractFileResult] = {k: v for (k, v) in self._results.items() if v.unique_name == filesystem_result}
                                    if bool(results):
                                        potential_imported_result = results[list(results.keys())[0]]
                                        potential_imported_results.append(potential_imported_result)
   
                                for potential_imported_result in potential_imported_results:
                                    
                                    preprocessed_golang_source = potential_imported_result.preprocessed_source
                                    
                                    # now we get all possible function and struct names
                                    funcs = self.compiled_func_grammar.findall(preprocessed_golang_source)
                                    funcs = [x for x in funcs if x]

                                    structs = self.compiled_struct_grammar.findall(preprocessed_golang_source)
                                    structs = [x for x in structs if x]
                                    all_tokens = structs + funcs
                                    
                                    # check if any of those tokes is contained in the source of the new dependency
                                    should_add_dependency = False
                                    for possibe_token in all_tokens:
                                        if possibe_token in result.preprocessed_source:
                                            should_add_dependency = True
                                            break
                                    
                                    if should_add_dependency is True:
                                        result.scanned_import_dependencies.append(potential_imported_result.unique_name)
                                        LOGGER.debug(f'adding import: {potential_imported_result.unique_name}')
                                        dependency_is_resolved = True

                        if dependency_is_resolved is False:
                            result.scanned_import_dependencies.append(dependency)
                            LOGGER.debug(f'adding import: {dependency}')
                            
                    else:
                        result.scanned_import_dependencies.append(dependency)
                        LOGGER.debug(f'adding import: {dependency}')

                else:
                    result.scanned_import_dependencies.append(dependency)
                    LOGGER.debug(f'adding import: {dependency}')

    
    def _add_package_name_to_result(self, result: FileResult):
        result.module_name = ""


if __name__ == "__main__":
    LEXER = GoParser()
    print(f'{LEXER.results=}')
