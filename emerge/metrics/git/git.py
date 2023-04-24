"""
Contains the implementation of git metrics, based on results from PyDriller (https://github.com/ishepard/pydriller).
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, List, Any
from enum import auto
import logging
import os

from pydriller import Repository

import coloredlogs

from emerge.analysis import Analysis

# interfaces for inputs
from emerge.abstractresult import AbstractResult
from emerge.log import Logger

# enums and interface/type of the given metric
from emerge.metrics.abstractmetric import EnumLowerKebabCase
from emerge.metrics.metrics import CodeMetric


LOGGER = Logger(logging.getLogger('metrics'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class GitMetrics(CodeMetric):

    class Keys(EnumLowerKebabCase):
        COMMIT_METRICS = auto()

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)

        self.alanysis = analysis
        self.git_directory = analysis.git_directory

        self.number_of_commits = 0
        self.latest_commit_date: Any = None
        self.earliest_commit_date: Any = None

        self.commit_dates: List[Any] = []
        self.commit_hashes: List[Any] = []
        self.change_results: List[Any] = []
        self.last_number_of_commits_for_calculation = 600

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        self._calculate_git_metrics()
        self._setup_commit_dates()
        self._calculate_local_metric_data(results)
        self._calculate_global_metric_data(results)

    def _setup_commit_dates(self):
        repository = Repository(self.analysis.git_directory, order='reverse')

        processed_commits = 0
        for commit in repository.traverse_commits():
            if processed_commits >= self.last_number_of_commits_for_calculation:
                break

            self.number_of_commits += 1
            self.commit_dates.append(commit.committer_date)
            self.commit_hashes.append(commit.hash)

        if self.number_of_commits > 0:
            self.latest_commit_date = self.commit_dates[0]
            self.earliest_commit_date = self.commit_dates[-1]

    def _calculate_git_metrics(self):
        repository = Repository(self.analysis.git_directory, order='reverse')

        processed_commits = 0
        for commit in repository.traverse_commits():
            if processed_commits >= self.last_number_of_commits_for_calculation:
                break

            file_array = []
            file_churn = {}

            if len(commit.modified_files) == 0:
                continue

            for file in commit.modified_files:
                _, file_extension = os.path.splitext(file.filename)
                if file_extension in self.analysis.only_permit_file_extensions:
                    file_array.append(file.filename)

                    # calc code churn per file, assuming it's the sum of all changed lines
                    file_churn[file.filename] = file.added_lines + file.deleted_lines

                else:
                    LOGGER.debug(f'ignoring not allowed file extension: {file_extension} in commit {commit.hash}...')

            if len(file_array) > 0:
                change_result = {
                    "hash": commit.hash,
                    "date": commit.committer_date.strftime("%Y-%m-%d"),
                    "files": file_array,
                    "churn": file_churn
                }

                self.change_results.append(change_result)

            processed_commits = processed_commits + 1
        
        self.change_results.reverse()

    def _calculate_local_metric_data(self, results: Dict[str, AbstractResult]):
        pass

    def _calculate_global_metric_data(self, results: Dict[str, AbstractResult]):  # pylint: disable=unused-argument
        LOGGER.debug(f'calculating average method count {self.metric_name}...')
        self.overall_data[self.Keys.COMMIT_METRICS.value] = self.change_results
        pass  # pylint: disable=unnecessary-pass
