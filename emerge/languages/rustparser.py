"""
Contains the implementation of the Rust language parser (tree-sitter based dependency extraction).
"""

from typing import Dict
import logging
import os
from pathlib import Path

import coloredlogs

from emerge.languages.abstractparser import AbstractParser, ParsingMixin, Parser, CoreParsingKeyword, LanguageType
from emerge.languages.rust_treesitter import extract_rust_module_dependencies
from emerge.results import FileResult
from emerge.abstractresult import AbstractResult, AbstractFileResult, AbstractEntityResult
from emerge.stats import Statistics
from emerge.log import Logger

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class RustParser(AbstractParser, ParsingMixin):

    def __init__(self):
        self._results: Dict[str, AbstractResult] = {}

    @classmethod
    def parser_name(cls) -> str:
        return Parser.RUST_PARSER.name

    @classmethod
    def language_type(cls) -> str:
        return LanguageType.RUST.name

    @property
    def results(self) -> Dict[str, AbstractResult]:
        return self._results

    @results.setter
    def results(self, value):
        self._results = value

    def generate_file_result_from_analysis(self, analysis, *, file_name: str, full_file_path: str, file_content: str) -> None:
        LOGGER.debug('generating file results...')
        scanned_tokens = self.preprocess_file_content_and_generate_token_list(file_content)

        relative_file_path_to_analysis = self.create_relative_analysis_file_path(analysis.source_directory, full_file_path)

        file_result = FileResult.create_file_result(
            analysis=analysis,
            scanned_file_name=file_name,
            relative_file_path_to_analysis=relative_file_path_to_analysis,
            absolute_name=full_file_path,
            display_name=relative_file_path_to_analysis,
            module_name="",
            scanned_by=self.parser_name(),
            scanned_language=LanguageType.RUST,
            scanned_tokens=scanned_tokens,
            source=file_content,
            preprocessed_source=""
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

        try:
            specifiers = extract_rust_module_dependencies(result.source)
        except Exception as ex:  # pylint: disable=broad-except
            result.analysis.statistics.increment(Statistics.Key.PARSING_MISSES)
            LOGGER.warning(f'tree-sitter extraction failed for {result.scanned_file_name}: {ex}')
            return

        for dependency in specifiers:
            analysis.statistics.increment(Statistics.Key.PARSING_HITS)
            resolved_dependency = self.try_resolve_dependency(dependency, result, analysis)

            if self._is_dependency_in_ignore_list(resolved_dependency, analysis):
                LOGGER.debug(f'ignoring dependency from {result.unique_name} to {resolved_dependency}')
            else:
                result.scanned_import_dependencies.append(resolved_dependency)
                LOGGER.debug(f'adding import: {resolved_dependency} to {result.unique_name}')

    def _project_parent(self, analysis) -> Path:
        return Path(analysis.source_directory).parent

    def _exists_under_project(self, analysis, relative_analysis_dependency: str) -> bool:
        return os.path.exists(self._project_parent(analysis) / relative_analysis_dependency)

    def try_resolve_dependency(self, dependency: str, result: AbstractFileResult, analysis) -> str:
        if analysis.import_aliases_available:
            renamed = self.replace_substring_if_any_mapping_key_in_string_exists(dependency, analysis.import_aliases)
            if renamed != dependency:
                LOGGER.info(f'renamed dependency: {dependency} -> {renamed}')
                dependency = renamed

        if dependency.startswith("./"):
            sub = dependency[2:]
            rs_path = self.create_relative_analysis_path_for_dependency(f"{sub}.rs", str(result.relative_analysis_path))
            if self._exists_under_project(analysis, rs_path):
                return rs_path
            mod_path = self.create_relative_analysis_path_for_dependency(f"{sub}/mod.rs", str(result.relative_analysis_path))
            if self._exists_under_project(analysis, mod_path):
                return mod_path
            return rs_path

        if dependency.startswith("crate::"):
            rel = dependency[len("crate::") :].replace("::", "/")
            parts = rel.split("/")
            for i in range(len(parts), 0, -1):
                prefix = "/".join(parts[:i])
                rs_candidate = f"{prefix}.rs"
                if self._exists_under_project(analysis, rs_candidate):
                    return rs_candidate
                mod_candidate = f"{prefix}/mod.rs"
                if self._exists_under_project(analysis, mod_candidate):
                    return mod_candidate
            return f"{rel}.rs"

        if dependency.startswith("super::"):
            dep = dependency
            parent_path = str(result.relative_analysis_path)
            while dep.startswith("super::"):
                dep = dep[len("super::") :]
                parent_path = str(Path(parent_path).parent)
            rel_path = dep.replace("::", "/")
            rs_candidate = self.create_relative_analysis_path_for_dependency(f"{rel_path}.rs", parent_path)
            if self._exists_under_project(analysis, rs_candidate):
                return rs_candidate
            mod_candidate = self.create_relative_analysis_path_for_dependency(f"{rel_path}/mod.rs", parent_path)
            if self._exists_under_project(analysis, mod_candidate):
                return mod_candidate
            return rs_candidate

        if dependency.startswith("self::"):
            rel = dependency[len("self::") :].replace("::", "/")
            rs_candidate = self.create_relative_analysis_path_for_dependency(f"{rel}.rs", str(result.relative_analysis_path))
            if self._exists_under_project(analysis, rs_candidate):
                return rs_candidate
            mod_candidate = self.create_relative_analysis_path_for_dependency(f"{rel}/mod.rs", str(result.relative_analysis_path))
            if self._exists_under_project(analysis, mod_candidate):
                return mod_candidate
            return rs_candidate

        if CoreParsingKeyword.SLASH.value in dependency or CoreParsingKeyword.DOT.value in dependency:
            dependency = self.resolve_relative_dependency_path(
                dependency, str(result.absolute_dir_path), analysis.source_directory
            )

        return dependency

    def _add_package_name_to_result(self, result: AbstractResult):
        LOGGER.warning(f'currently not supported in {self.parser_name}')


if __name__ == "__main__":
    LEXER = RustParser()
    print(f'{LEXER.results=}')
