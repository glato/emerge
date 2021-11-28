"""
Contains a statistics class which can gather/output local and global result and scan statistics.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, Any
from enum import Enum, unique, auto
import logging
import coloredlogs

from emerge.log import Logger

LOGGER = Logger(logging.getLogger('analysis'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class Statistics:
    """Simple statistics gathering class, which is basically a big, wrapped dictionary with some convenience keys and methods.
    """

    def __init__(self):
        self.data: Dict[str, Any] = {}

    @unique
    class Key(Enum):
        """Small embedded class that contains all valid keys for statistics.
        """
        SCANNED_FILES = auto()
        SKIPPED_FILES = auto()
        SCANNING_RUNTIME = auto()
        TOTAL_RUNTIME = auto()
        ANALYSIS_DATE = auto()
        FILE_RESULTS_CREATION_RUNTIME = auto()
        ENTITY_RESULTS_CREATION_RUNTIME = auto()
        ANALYSIS_RUNTIME = auto()
        METRIC_CALCULATION_RUNTIME = auto()
        EXTRACTED_FILE_RESULTS = auto()
        EXTRACTED_ENTITY_RESULTS = auto()
        PARSING_HITS = auto()
        PARSING_MISSES = auto()
        RUNTIME = auto()

    def add(self, *, key, value: Any, prefix: str = None) -> None:
        if prefix is not None:
            if (k := prefix + '-' + key.name.lower()) not in self.data:
                self.data[k] = value
        else:
            if (k := key.name.lower()) not in self.data:
                self.data[k] = value

    def update(self, *, key, value: Any) -> None:
        self.data[key.name.lower()] = value

    def increment(self, key) -> None:
        if (k := key.name.lower()) not in self.data:
            self.data[k] = 1
        else:
            self.data[k] += 1
