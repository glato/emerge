"""
Contains simple logging wrapper and logging related helper classes.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from enum import Enum, unique, auto
import logging

import coloredlogs


ALL_LOGGERS = ['parser', 'metrics', 'config', 'analysis', 'graph', 'emerge']
logging.addLevelName(logging.DEBUG, 'D')
logging.addLevelName(logging.INFO, 'I')
logging.addLevelName(logging.ERROR, 'E')


@unique
class LogLevel(Enum):
    ERROR = 3
    INFO = 6
    DEBUG = 7


@unique
class LogState(Enum):
    ON = auto()
    OFF = auto()


class Logger:
    """A simple ✅-driven logger class that can log messages in a nice way related to the log level.
    """
    level: LogLevel = LogLevel.ERROR
    state: LogState = LogState.ON
    log_format: str = '%(asctime)s ' + '%(name)+10s' + ' %(levelname)s %(message)s'

    """Enable overriding the log level if a command line argument was used."""
    override_level_from_command_line_arg = False

    def __init__(self, logger):
        self._logger = logger

    def info(self, message: str):
        self._logger.info("\U000023E9" + " " + message)

    def info_start(self, message: str):
        self._logger.info("\U0001F449" + " " + message)

    def debug(self, message: str):
        self._logger.debug("\U000023E9" + " " + message)

    def error(self, message: str):
        self._logger.error("\U00002757" + " " + message)

    def warning(self, message: str):
        self._logger.debug("\U00002753" + " " + message)

    def info_done(self, message: str):
        self._logger.info("\U00002705" + " " + message)

    def logger(self):
        return self._logger

    @staticmethod
    def set_log_level(level: LogLevel):
        """Sets the current log level.

        Args:
            level (LogLevel): The given log level.
        """
        if level == LogLevel.DEBUG:
            Logger.set_logging_level_to_debug()
        if level == LogLevel.INFO:
            Logger.set_logging_level_to_info()
        if level == LogLevel.ERROR:
            Logger.set_logging_level_to_error()

    @staticmethod
    def level_is_at_least(level: LogLevel) -> bool:
        """Checks if the current log level at least equals the given level.

        Returns:
            bool: True if the current level is at least the given log level, otherwise False.
        """
        if level.value >= Logger.level.value:
            return True
        return False

    @staticmethod
    def activate_logging():
        """Activates logging.
        """
        Logger.state = LogState.ON
        for logger_name in ALL_LOGGERS:
            my_logger = logging.getLogger(logger_name)
            my_logger.disabled = False

    @staticmethod
    def deactivate_logging():
        """Deactivates logging.
        """
        Logger.state = LogState.OFF
        for logger_name in ALL_LOGGERS:
            my_logger = logging.getLogger(logger_name)
            my_logger.disabled = True

    @staticmethod
    def set_logging_level_to_info():
        """Convenience method to set the level of all loggers to info level.
        """
        Logger.level = LogLevel.INFO
        for logger_name in ALL_LOGGERS:
            my_logger = logging.getLogger(logger_name)
            my_logger.setLevel(logging.INFO)
            Logger.level = LogLevel.INFO
            new_logger = Logger(logging.getLogger(logger_name))
            coloredlogs.install(level='INFO', logger=new_logger.logger(), fmt=Logger.log_format)

    @staticmethod
    def set_logging_level_to_debug():
        """Convenience method to set the level of all loggers to debug level.
        """
        Logger.level = LogLevel.DEBUG
        for logger_name in ALL_LOGGERS:
            my_logger = logging.getLogger(logger_name)
            my_logger.setLevel(logging.DEBUG)
            Logger.level = LogLevel.DEBUG
            new_logger = Logger(logging.getLogger(logger_name))
            coloredlogs.install(level='DEBUG', logger=new_logger.logger(), fmt=Logger.log_format)

    @staticmethod
    def set_logging_level_to_error():
        """Convenience method to set the level of all loggers to error level.
        """
        Logger.level = LogLevel.ERROR
        for logger_name in ALL_LOGGERS:
            my_logger = logging.getLogger(logger_name)
            my_logger.setLevel(logging.ERROR)
            Logger.level = LogLevel.ERROR
            new_logger = Logger(logging.getLogger(logger_name))
            coloredlogs.install(level='ERROR', logger=new_logger.logger(), fmt=Logger.log_format)
