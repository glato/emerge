"""
Contains all abstract parsing classes and relevant enums.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import re
import logging

from abc import ABC, abstractmethod
from enum import Enum, unique, auto
from typing import Dict, List, Generator, Optional, Tuple
from pathlib import Path
import coloredlogs

from emerge.abstractresult import AbstractResult, AbstractEntityResult
from emerge.log import Logger

LOGGER = Logger(logging.getLogger('parser'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class LanguageType(Enum):
    JAVA = auto()
    KOTLIN = auto()
    OBJC = auto()
    SWIFT = auto()
    RUBY = auto()
    GROOVY = auto()
    JAVASCRIPT = auto()
    TYPESCRIPT = auto()
    C = auto()
    CPP = auto()
    PY = auto()
    GO = auto()


@unique
class Parser(Enum):
    JAVA_PARSER = auto()
    KOTLIN_PARSER = auto()
    OBJC_PARSER = auto()
    SWIFT_PARSER = auto()
    C_PARSER = auto()
    CPP_PARSER = auto()
    JAVASCRIPT_PARSER = auto()
    TYPESCRIPT_PARSER = auto()
    RUBY_PARSER = auto()
    GROOVY_PARSER = auto()
    PYTHON_PARSER = auto()
    GO_PARSER = auto()


@unique
class CoreParsingKeyword(Enum):
    ENTITY_NAME = "entity_name"
    LINE_COMMENT = "line_comment"
    START_BLOCK_COMMENT = "start_block_comment"
    STOP_BLOCK_COMMENT = "stop_block_comment"
    INHERITED_ENTITY_NAME = "inherited_entity_name"
    IMPORT_ENTITY_NAME = "import_entity_name"
    IMPORT_PATH = "import_path"
    COLON = ":"
    SEMICOLON = ";"
    DOT = "."
    COMMA = ","
    SLASH = "/"
    SINGLE_QUOTE = "'"
    DOUBLE_QUOTE = '"'
    UNDERSCORE = "_"
    OPENING_ANGLE_BRACKET = "<"
    CLOSING_ANGLE_BRACKET = ">"
    ASTERISK = "*"
    OPENING_CURVED_BRACKET = "{"
    CLOSING_CURVED_BRACKET = "}"
    AT = "@"
    DASH = "-"
    OPENING_ROUND_BRACKET = "("
    CLOSING_ROUND_BRACKET = ")"
    POSIX_CURRENT_DIRECTORY = "./"
    POSIX_PARENT_DIRECTORY = "../"
    NEWLINE = "\n"


class ParsingMixin(ABC):

    class Constants(Enum):
        MAX_DEBUG_TOKENS_READAHEAD = 10

    @staticmethod
    def resolve_relative_dependency_path(relative_analysis_dependency_path: str, result_absolute_dir_path: str, analysis_source_directory: str) -> str:
        """Creates the absolute path for a dependency and try to resolve it with pathlib."""

        resolved_dependency = relative_analysis_dependency_path
        try:
            unresolved_path = f'{result_absolute_dir_path}/{relative_analysis_dependency_path}'
            resolved_path = f'{Path(unresolved_path).resolve()}'

            project_scanning_path = analysis_source_directory
            if project_scanning_path[-1] != CoreParsingKeyword.SLASH.value:  # add trailing '/' to project scanning path if necessary
                project_scanning_path = f"{project_scanning_path}{CoreParsingKeyword.SLASH.value}"

            # if the resolved path is still inside the project path, try to construct a full dependency path
            # which is only relative to the project_scanning_path
            if project_scanning_path in resolved_path:
                resolved_relative_analysis_dependency_path = str(resolved_path).replace(
                    f"{Path(analysis_source_directory).parent}{CoreParsingKeyword.SLASH.value}", "")

                resolved_dependency = resolved_relative_analysis_dependency_path
        # pylint: disable=broad-except
        except Exception as ex:
            LOGGER.warning(f'{ex}')

        return resolved_dependency

    @staticmethod
    def create_relative_analysis_path_for_dependency(dependency: str, relative_analysis_path: str) -> str:
        return f"{relative_analysis_path}/{dependency}"

    @staticmethod
    def any_mapping_key_in_string(string: str, mapping: Dict [str, str]) -> Optional[Tuple]:
        for key, value in mapping.items():
            if key in string:
                return key, value
        return None

    @staticmethod
    def replace_substring_if_any_mapping_key_in_string_exists(string: str, mapping: Dict[str, str]) -> str:
        exists = ParsingMixin.any_mapping_key_in_string(string, mapping)
        if exists is not None:
            key, value = exists
            return string.replace(key, value) 
        return string

    @staticmethod
    def create_relative_analysis_file_path(analysis_source_directory: str, full_file_path: str) -> str:
        parent_analysis_source_path = f"{Path(analysis_source_directory).parent}/"
        relative_file_path_to_analysis = full_file_path.replace(parent_analysis_source_path, "")
        return relative_file_path_to_analysis

    @classmethod
    def create_before_and_ahead_string(cls, obj, previous, following) -> str:
        read_before_and_ahead = []
        if previous is not None:
            read_before_and_ahead = previous  # or previous[-5:]
        read_before_and_ahead.append(obj)
        read_before_and_ahead += following  # or += following[:5]
        return " ".join(read_before_and_ahead)

    @staticmethod
    def _gen_word_read_ahead(list_of_words) -> Generator:
        following = None
        length = len(list_of_words)
        for index, obj in enumerate(list_of_words):
            if index < (length - 1):
                following = list_of_words[index + 1:]
            yield index, obj, following

    @staticmethod
    def _gen_word_before_and_read_ahead(list_of_words) -> Generator:
        previous = following = None
        length = len(list_of_words)
        for index, obj in enumerate(list_of_words):
            if index > 0:
                previous = list_of_words[:index]
            if index < (length - 1):
                following = list_of_words[index + 1:]
            yield index, obj, previous, following

    @staticmethod
    def _filter_source_tokens_without_comments(list_of_words, line_comment_string, start_comment_string, stop_comment_string) -> str:
        source = " ".join(list_of_words)
        source_lines = source.splitlines()
        source_lines_without_comments = []
        active_block_comment = False

        for line in source_lines:
            if start_comment_string in line:
                active_block_comment = True
                continue
            if stop_comment_string in line:
                active_block_comment = False
                continue
            if line.strip().startswith(line_comment_string):
                continue

            if not active_block_comment:
                source_lines_without_comments.append(line)

        return "\n".join(source_lines_without_comments)

    def read_input_from_file(self, path_with_file_name) -> str:
        with open(path_with_file_name, encoding="ISO-8859-1") as file:
            file_content = file.read()
            return file_content

    @classmethod
    def create_read_ahead_string(cls, obj, following) -> str:
        read_ahead = [obj]
        read_ahead += following
        return " ".join(read_ahead)

    @staticmethod
    def _is_dependency_in_ignore_list(dependency: str, analysis) -> bool:
        if bool(analysis.ignore_dependencies_containing):
            ignored_dependency: str
            for ignored_dependency in analysis.ignore_dependencies_containing:
                if ignored_dependency.lower() in dependency.lower():
                    return True
        return False

    @staticmethod
    def is_entity_in_ignore_list(entity: str, analysis) -> bool:
        if bool(analysis.ignore_entities_containing):
            for ignored_entity in analysis.ignore_entities_containing:
                if ignored_entity in entity:
                    return True
        return False

    @classmethod
    def preprocess_file_content_and_generate_token_list(cls, file_content: str) -> List[str]:
        return re.findall(r'\S+|\n', file_content.replace(':', ' : ')
                                                 .replace(';', ' ; ')
                                                 .replace('{', ' { ')
                                                 .replace('}', ' } ')
                                                 .replace('(', ' ( ')
                                                 .replace(')', ' ) ')
                                                 .replace('[', ' [ ')
                                                 .replace(']', ' ] ')
                                                 .replace('?', ' ? ')
                                                 .replace('!', ' ! ')
                                                 .replace(',', ' , ')
                                                 .replace('<', ' < ')
                                                 .replace('>', ' > ')
                          )

    @classmethod
    def preprocess_file_content_and_generate_token_list_by_mapping(cls, file_content: str, mapping_dict: Dict[str, str]) -> List[str]:
        for origin, mapped in mapping_dict.items():
            file_content = file_content.replace(origin, mapped)
        return re.findall(r'\S+|\n', file_content)


class AbstractParser(ParsingMixin, ABC):

    @property
    @abstractmethod
    def results(self) -> Dict[str, AbstractResult]:
        ...

    # pylint: disable=unused-argument
    @results.setter
    def results(self, value):
        ...

    @classmethod
    @abstractmethod
    def parser_name(cls) -> str:
        ...

    @classmethod
    @abstractmethod
    def language_type(cls) -> str:
        ...

    @abstractmethod
    def generate_entity_results_from_analysis(self, analysis) -> None:
        ...

    @abstractmethod
    def generate_file_result_from_analysis(self, analysis, *, file_name: str, full_file_path: str, file_content: str) -> None:
        ...

    @abstractmethod
    def after_generated_file_results(self, analysis) -> None:
        ...

    @abstractmethod
    def create_unique_entity_name(self, entity: AbstractEntityResult) -> None:
        ...
