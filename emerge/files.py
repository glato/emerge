"""
Handles all mappings to languages and relevant file extensions.
Contains FileManager to handle filesystem specific functionality.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from enum import Enum, unique, auto
from typing import Optional

import os
import shutil
import logging

import coloredlogs
from emerge.languages.goparser import GoParser

from emerge.languages.javaparser import JavaParser
from emerge.languages.swiftparser import SwiftParser
from emerge.languages.cparser import CParser
from emerge.languages.cppparser import CPPParser
from emerge.languages.groovyparser import GroovyParser
from emerge.languages.javascriptparser import JavaScriptParser
from emerge.languages.typescriptparser import TypeScriptParser
from emerge.languages.kotlinparser import KotlinParser
from emerge.languages.objcparser import ObjCParser
from emerge.languages.rubyparser import RubyParser
from emerge.languages.pyparser import PythonParser

from emerge.log import Logger

LOGGER = Logger(logging.getLogger('emerge'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


@unique
class FileScanType(Enum):
    FILE = auto()
    ENTITY = auto()


@unique
class LanguageExtension(Enum):
    JAVA = '.java'
    SWIFT = '.swift'
    C = '.c'
    CPP = '.cpp'
    GROOVY = '.groovy'
    JAVASCRIPT = '.js'
    JSX = '.jsx'
    TYPESCRIPT = '.ts'
    TSX = '.tsx'
    KOTLIN = '.kt'
    OBJC = '.m'
    RUBY = '.rb'
    C_HEADER = '.h'
    PYTHON = '.py'
    GO = '.go'

    @staticmethod
    def valid_key(key) -> bool:
        if any(x for x in LanguageExtension if x.name.lower() == key.lower()):
            return True
        else:
            return False

    @classmethod
    def key_for_value(cls, value):
        return str(LanguageExtension(value)).replace(cls.__name__ + '.', '').lower()

    @classmethod
    def value_exists(cls, value) -> bool:
        try:
            LanguageExtension(value)
            return True
        except: # pylint: disable=bare-except
            return False


class FileScanMapper:
    @staticmethod
    def choose_parser(file_extension, only_permit_languages=None) -> Optional[str]:
        """
        Returns:
            Optional[str]: Returns a parser name, if a matching of file extension/parser can be found, otherwise None.
        """
        if file_extension == LanguageExtension.JAVA.value:
            return JavaParser.parser_name()
        if file_extension == LanguageExtension.SWIFT.value:
            return SwiftParser.parser_name()
        if file_extension == LanguageExtension.C.value:
            return CParser.parser_name()
        if file_extension == LanguageExtension.CPP.value:
            return CPPParser.parser_name()
        if file_extension == LanguageExtension.GROOVY.value:
            return GroovyParser.parser_name()
        if file_extension == LanguageExtension.JAVASCRIPT.value or file_extension == LanguageExtension.JSX.value:
            return JavaScriptParser.parser_name()
        if file_extension == LanguageExtension.TYPESCRIPT.value or file_extension == LanguageExtension.TSX.value:
            return TypeScriptParser.parser_name()
        if file_extension == LanguageExtension.KOTLIN.value:
            return KotlinParser.parser_name()
        if file_extension == LanguageExtension.OBJC.value:
            return ObjCParser.parser_name()
        if file_extension == LanguageExtension.RUBY.value:
            return RubyParser.parser_name()
        if file_extension == LanguageExtension.PYTHON.value:
            return PythonParser.parser_name()
        if file_extension == LanguageExtension.GO.value:
            return GoParser.parser_name()
        if file_extension == LanguageExtension.C_HEADER.value:
            if only_permit_languages:
                if 'objc' in only_permit_languages:
                    return ObjCParser.parser_name()
                if 'c' in only_permit_languages:
                    return CParser.parser_name()
                if 'cpp' in only_permit_languages:
                    return CPPParser.parser_name()

        return None


class FileManager:
    @staticmethod
    def copy_force_graph_template_to_export_dir(target_export_path: str):
        """Performs a recursive copy of the HTML/d3 template located in /output/html to a given export path."""

        origin_output_subpath = "/output"
        origin_force_graph_subpath = "/html"

        # get the full path of emerge.py / https://stackoverflow.com/questions/5137497/find-current-directory-and-files-directory
        origin_emerge_base_path = os.path.dirname(os.path.realpath(__file__))

        origin_complete_path = origin_emerge_base_path + origin_output_subpath + origin_force_graph_subpath
        target_complete_path = target_export_path + origin_force_graph_subpath

        if os.path.isdir(target_complete_path):
            try:
                shutil.rmtree(target_complete_path)
                
            except Exception as ex: # pylint: disable=broad-except
                LOGGER.error(f'{ex}')
        try:
            shutil.copytree(origin_complete_path, target_complete_path)
            LOGGER.info_done("generated d3 web app for your browser")
            
        except Exception as ex: # pylint: disable=broad-except
            LOGGER.error(f'{ex}')


def truncate_directory(directory: str) -> str:
    """Simple truncation of a given directory path as string."""

    if len(directory) > 50:
        split_directory = directory.split('/')
        prefix_truncated = '/'.join(directory.split('/')[len(split_directory)-5:])
        return '.../' + prefix_truncated
    else:
        return directory
