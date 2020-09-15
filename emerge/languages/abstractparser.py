"""
Contains all abstract parsing classes and relevant enums.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from abc import ABC, abstractmethod
from enum import Enum, unique, auto
from typing import Dict, List, Generator
from emerge.abstractresult import AbstractResult, AbstractEntityResult
import re
import coloredlogs
import logging
from emerge.logging import Logger

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
    C = auto()


@unique
class Parser(Enum):
    JAVA_PARSER = auto()
    KOTLIN_PARSER = auto()
    OBJC_PARSER = auto()
    SWIFT_PARSER = auto()
    C_PARSER = auto()
    JAVASCRIPT_PARSER = auto()
    RUBY_PARSER = auto()
    GROOVY_PARSER = auto()


@unique
class CoreParsingKeyword(Enum):
    ENTITY_NAME = "entity_name"
    LINE_COMMENT = "line_comment"
    START_BLOCK_COMMENT = "start_block_comment"
    STOP_BLOCK_COMMENT = "stop_block_comment"
    INHERITED_ENTITY_NAME = "inherited_entity_name"
    IMPORT_ENTITY_NAME = "import_entity_name"
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


class AbstractParsingCore(ABC):

    class Constants(Enum):
        MAX_DEBUG_TOKENS_READAHEAD = 10

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
    def _gen_word_read_ahead(list_of_words) -> Generator:
        following = None
        length = len(list_of_words)
        for index, obj in enumerate(list_of_words):
            if index < (length - 1):
                following = list_of_words[index + 1:]
            yield index, obj, following

    @staticmethod
    def _is_dependency_in_ignore_list(dependency: str, analysis) -> bool:
        if bool(analysis.ignore_dependencies_containing):
            for ignored_dependency in analysis.ignore_dependencies_containing:
                if ignored_dependency in dependency:
                    return True
        return False

    @classmethod
    def preprocess_file_content_and_generate_token_list(cls, file_content: str) -> List[str]:
        return re.findall(r'\S+|\n', file_content.replace(':', ' : ')
                                                 .replace(';', ' ; ')
                                                 .replace('{', ' { ')
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


class AbstractParser(AbstractParsingCore, ABC):

    @property
    @abstractmethod
    def results(self) -> Dict[str, AbstractResult]:
        ...

    @results.setter
    @abstractmethod
    def results(self, value):
        ...

    @classmethod
    @abstractmethod
    def parser_name(cls) -> str:
        ...

    @abstractmethod
    def generate_entity_results_from_analysis(self, analysis) -> None:
        ...

    @abstractmethod
    def generate_file_result_from_analysis(self, analysis, *, file_name: str, file_content: str) -> None:
        ...

    @abstractmethod
    def after_generated_file_results(self, analysis) -> None:
        ...

    @abstractmethod
    def create_unique_entity_name(self, *, entity: AbstractEntityResult) -> None:
        ...
