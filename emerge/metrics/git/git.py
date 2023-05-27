"""
Contains the implementation of git metrics, based on results from PyDriller (https://github.com/ishepard/pydriller).
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, List, Any
from enum import auto
import logging
import os

from itertools import combinations
from pathlib import Path

from pydriller import Repository

import coloredlogs

from emerge.analysis import Analysis

# interfaces for inputs
from emerge.abstractresult import AbstractResult
from emerge.log import Logger

# enums and interface/type of the given metric
from emerge.metrics.abstractmetric import EnumLowerKebabCase
from emerge.metrics.metrics import CodeMetric
from emerge.metrics.whitespace.whitespace import WhitespaceMetric


LOGGER = Logger(logging.getLogger('metrics'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)


class GitMetrics(CodeMetric):

    class Keys(EnumLowerKebabCase):
        COMMIT_METRICS = auto()

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)

        self.alanysis = analysis

        # pylint: disable=broad-exception-raised
        if analysis.git_directory == None:
            raise Exception('❗️ No git directory path found, please check in yaml config')

        self.git_directory = analysis.git_directory

        self.ws_complexity_metric = WhitespaceMetric(analysis)

        self.number_of_commits = 0
        self.latest_commit_date: Any = None
        self.earliest_commit_date: Any = None

        self.commit_dates: List[Any] = []
        self.commit_hashes: List[Any] = []
        self.change_results: List[Any] = []

        self.file_result_prefix = ""
        self.file_result_prefix_full = ""
        
        self.last_number_of_commits_for_calculation = analysis.git_commit_limit
        self.git_exclude_merge_commits = analysis.git_exclude_merge_commits

    def init(self):
        if self.analysis.source_directory and self.analysis.git_directory:
            if (self.analysis.source_directory != self.analysis.git_directory):

                self.file_result_prefix = self.analysis.source_directory.replace(self.analysis.git_directory + '/', "")
                self.file_result_prefix_full = self.file_result_prefix
                self.file_result_prefix = f'{Path(self.file_result_prefix).parent}'

                if self.file_result_prefix == '.':
                    self.file_result_prefix = ""

            else:
                self.file_result_prefix = "" # f'{Path(self.analysis.source_directory).name}'
                self.file_result_prefix_full = "" # self.analysis.source_directory.replace(os.path.dirname(self.analysis.source_directory) + "/", "")
                pass

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        self.init()
        self._calculate_git_metrics(results)
        self._setup_commit_dates()
        self._calculate_local_metric_data(results)
        self._calculate_global_metric_data(results)

    def _setup_commit_dates(self):
        repository = Repository(self.analysis.git_directory, order='reverse', only_no_merge=self.git_exclude_merge_commits)

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

    def _calculate_git_metrics(self, results):
        results_keys = list(results.keys())
        repository = Repository(self.analysis.git_directory, order='reverse', only_no_merge=self.git_exclude_merge_commits)
    
        temporal_edges_found = 0
        processed_commits = 0
        for commit in repository.traverse_commits():
            if processed_commits >= self.last_number_of_commits_for_calculation:
                break

            file_array = []
            filepath_array = []
            d3_links_array = []
            file_churn = {}
            ws_complexity = {}
            sloc = {}
            author = ""
            filepath_author_map = {}

            try:
                if len(commit.modified_files) == 0:
                    continue
            except ValueError:
                LOGGER.info('ignoring git error, keep going...')
                continue

            for file in commit.modified_files:
                _, file_extension = os.path.splitext(file.filename)
                if file_extension in self.analysis.only_permit_file_extensions:

                    # check if the commit is relevant for the metrics, i.e. check if it includes at least one file that is contained in the analysis scan
                    if file.new_path is not None:
                        prefixed_file_path = file.new_path.replace(self.file_result_prefix, '').lstrip('/')

                        found = False
                        for key in results_keys:
                            if prefixed_file_path in key:
                                found = True

                        if not found:
                            continue
                       
                    if file.new_path is not None:
                        file_array.append(file.filename)

                    if file.new_path is not None:
                        filepath_array.append(file.new_path)                        

                    # calc code churn per file, assuming it's the sum of all changed lines
                    file_churn[file.new_path] = file.added_lines + file.deleted_lines

                    # if the file has any source code, calc the ws complexity
                    if file.source_code:
                        ws_complexity[file.new_path] = self.ws_complexity_metric.calulate_from_source(file.source_code)
                        sloc[file.new_path] = file.nloc

                    if commit.author.email:
                        author = commit.author.email

                        if file.new_path is not None:

                            if file.new_path in filepath_author_map:
                                filepath_author_map[file.new_path][author] = file_churn[file.new_path]
                            else:
                                filepath_author_map[file.new_path] = {}
                                filepath_author_map[file.new_path][author] = file_churn[file.new_path]
                        
                else:
                    LOGGER.debug(f'ignoring not allowed file extension: {file_extension} in commit {commit.hash}...')

            if len(file_array) > 0:

                possible_edges = list(combinations(filepath_array, 2))
                
                if len(file_array) > 1:
                    pass

                for edge in possible_edges:
                    source = target = ""
                    prefixed_source_edge = edge[0].replace(self.file_result_prefix, '').lstrip('/')
                    prefixed_target_edge = edge[-1].replace(self.file_result_prefix, '').lstrip('/')

                    source_edge_in_results = any(prefixed_source_edge in x for x in results_keys)
                    target_edge_in_results = any(prefixed_target_edge in x for x in results_keys)

                    if source_edge_in_results:
                        source = prefixed_source_edge
                    if target_edge_in_results:
                        target = prefixed_target_edge

                    if source and target:
                        link = {"source" : source, "target" : target, "temporal": True}
                        d3_links_array.append(link)
                        temporal_edges_found += 1
                        source = target = ""
                        # LOGGER.info(f'temporal edge found: {link}')

                change_result = {
                    "hash": commit.hash,
                    "date": commit.committer_date.strftime("%d/%m/%Y"),
                    "exact_date": commit.committer_date.strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
                    "files": file_array,
                    "filepaths": filepath_array,
                    "links": d3_links_array,
                    "churn": file_churn,
                    "ws_complexity": ws_complexity,
                    "sloc": sloc,
                    "author": author,
                    "files_author_map": filepath_author_map,
                    "file_result_prefix": self.file_result_prefix,
                    "file_result_prefix_full": self.file_result_prefix_full
                }

                self.change_results.append(change_result)

                # only count relevant/ non-empty commits
                processed_commits = processed_commits + 1
        
        self.change_results.reverse()
        # LOGGER.info(f'temporal edges found: {temporal_edges_found}')

    def _calculate_local_metric_data(self, results: Dict[str, AbstractResult]):
        pass

    def _calculate_global_metric_data(self, results: Dict[str, AbstractResult]):  # pylint: disable=unused-argument
        LOGGER.debug(f'calculating average method count {self.metric_name}...')
        self.overall_data[self.Keys.COMMIT_METRICS.value] = self.change_results
        pass  # pylint: disable=unnecessary-pass
