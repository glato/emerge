"""
Contains the implementation of git metrics, based on results from PyDriller (https://github.com/ishepard/pydriller).
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, Pattern
from enum import auto
import logging
from datetime import datetime

from pydriller import Repository
from pydriller.metrics.process.code_churn import CodeChurn

import coloredlogs

from emerge.analysis import Analysis

# interfaces for inputs
from emerge.abstractresult import AbstractResult, AbstractFileResult, AbstractEntityResult
from emerge.log import Logger

# enums and interface/type of the given metric
from emerge.metrics.abstractmetric import EnumLowerKebabCase
from emerge.metrics.metrics import CodeMetric


LOGGER = Logger(logging.getLogger('metrics'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)

# put it in a global js dict, not per node since we need to pick those metrics related to the selected time range
{
    'commit_hash_1' : {
        'code_churn_in_file' : {
            'file1' : 123,
            'file2' : 456
        },
        'files:' : [
            'file1', 'file2'
        ],
        'author' : 'author1'
    },
}

class GitMetrics(CodeMetric):

    class Keys(EnumLowerKebabCase):
        CODE_CHURN_IN_FILE = auto()

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)

        self.repository = Repository(analysis.git_directory)

        self.number_of_commits = 0
        self.latest_commit_date = None
        self.earliest_commit_date = None

        # commit_dates = []
        # commit_hashes = []
        # for commit in self.repository.traverse_commits():
        #     self.number_of_commits += 1
            
        #     commit_dates.append(commit.committer_date)
        #     commit_hashes.append(commit.hash)
        
        # if self.number_of_commits > 0:
        #     self.latest_commit_date = commit_dates[0]
        #     self.earliest_commit_date = commit_dates[-1]

        #     metric = CodeChurn(path_to_repo=analysis.git_directory,
        #             from_commit=commit_hashes[0],
        #             to_commit=commit_hashes[1],
        #             add_deleted_lines_to_churn=True)
        #     files_count = metric.count()
        #     files_max = metric.max()
        #     files_avg = metric.avg()
        #     print('Total code churn for each file: {}'.format(files_count))
            

        # pass

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        self._calculate_local_metric_data(results)
        self._calculate_global_metric_data(results)

    def _calculate_code_churn(self):
        pass


    def _calculate_local_metric_data(self, results: Dict[str, AbstractResult]):
        for _, result in results.items():
            LOGGER.debug(f'calculating metric {self.pretty_metric_name} for result {result.unique_name}')


            # result.metrics[self.Keys.NUMBER_OF_METHODS_IN_ENTITY.value] = number_of_methods
            # self.local_data[result.unique_name] = {self.Keys.NUMBER_OF_METHODS_IN_ENTITY.value: number_of_methods}
            LOGGER.debug(f'calculation done, updated metric data of {result.unique_name}: {result.metrics=}')

    def _calculate_global_metric_data(self, results: Dict[str, AbstractResult]):
        LOGGER.debug(f'calculating average method count {self.metric_name}...')

        entity_results = {k: v for (k, v) in results.items() if isinstance(v, AbstractEntityResult)}
        file_results = {k: v for (k, v) in results.items() if isinstance(v, AbstractFileResult)}

        if len(file_results) > 0:

            #self.overall_data[self.Keys.AVG_NUMBER_OF_METHODS_IN_FILE.value] = average_methods_in_file
            LOGGER.debug(f'average method count per file: ')

        if len(entity_results) > 0:
            
            #self.overall_data[self.Keys.AVG_NUMBER_OF_METHODS_IN_ENTITY.value] = average_methods_in_entity
            LOGGER.debug(f'average method count per entity: ')

    # def __get_expression(self, result: AbstractResult) -> Pattern:
    #     return self.compiled_re[result.scanned_language.name]

