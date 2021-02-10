"""
This module defines the main Emerge class, that contains all parsers and the current configuration.
All analyses get started from here.
"""
# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict
import coloredlogs
import logging
import datetime

from emerge.config import Configuration

from emerge.languages.abstractparser import AbstractParser
from emerge.languages.javaparser import JavaParser
from emerge.languages.swiftparser import SwiftParser
from emerge.languages.cparser import CParser
from emerge.languages.groovyparser import GroovyParser
from emerge.languages.javascriptparser import JavaScriptParser
from emerge.languages.kotlinparser import KotlinParser
from emerge.languages.objcparser import ObjCParser
from emerge.languages.rubyparser import RubyParser

from emerge.analyzer import Analyzer
from emerge.abstractresult import AbstractResult
from emerge.logging import Logger, LogLevel
from emerge.core import format_timedelta

LOGGER = Logger(logging.getLogger('emerge'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)

__version__ = '0.9.3'
__updated__ = '2021-02-10 22:11:36'


class Emerge:
    _version: str = f'{__version__} ({__updated__})'
    config = Configuration(_version)

    def __init__(self):
        """Initialize all collected results, available parsers and set the log level.
        """
        self._results: Dict[str, AbstractResult] = {}
        self._parsers: Dict[str, AbstractParser] = {
            JavaParser.parser_name(): JavaParser(),
            SwiftParser.parser_name(): SwiftParser(),
            CParser.parser_name(): CParser(),
            GroovyParser.parser_name(): GroovyParser(),
            JavaScriptParser.parser_name(): JavaScriptParser(),
            KotlinParser.parser_name(): KotlinParser(),
            ObjCParser.parser_name(): ObjCParser(),
            RubyParser.parser_name(): RubyParser()
        }
        self.set_log_level(LogLevel.ERROR)

    def parse_args(self):
        self.config.parse_args()

    def load_config(self, path):
        self.config.load_config_from_yaml_file(path)

    def print_config(self):
        self.config.print_config_as_yaml()
        self.config.print_config_dict()

    def get_config(self) -> Dict:
        return self.config.get_config_as_dict()

    def print_version(self):
        LOGGER.info(f'emerge version: {self.get_version()}')

    def start(self):
        """Starts emerge by parsing arguments/configuration and starting the analysis from an analyzer instance. 
        """
        start_time = datetime.datetime.now()

        self.parse_args()

        if self.config.has_valid_config_path():
            self.load_config(self.config.yaml_config_path)
            if self.config.valid == True:
                self.start_analyzing()
            else:
                LOGGER.error(f'will not start with any analysis due configuration errors')
                return

        stop_time = datetime.datetime.now()
        delta_total_runtime = stop_time - start_time
        total_runtime = format_timedelta(delta_total_runtime, '%H:%M:%S + %s ms')
        LOGGER.info_done(f'total runtime: {total_runtime}')

    def start_with_log_level(self, level: LogLevel):
        """Sets a custom log level and starts emerge.

        Args:
            level (LogLevel): A given log level.
        """
        Logger.set_log_level(level)
        self.start()

    def set_log_level(self, level: LogLevel):
        Logger.set_log_level(level)

    def start_analyzing(self):
        """Starts with the first analysis on an Analyzer instance.
        """
        analyzer = Analyzer(self.config, self._parsers)
        analyzer.start_analyzing()

    @staticmethod
    def get_version() -> str:
        return Emerge._version
