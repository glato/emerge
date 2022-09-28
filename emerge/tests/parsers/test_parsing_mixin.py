"""
All unit tests that are related to the ParsingMixin.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import unittest

from emerge.results import FileResult
from emerge.analysis import Analysis
from emerge.languages.abstractparser import LanguageType, ParsingMixin


class ParsingMixinTestCase(unittest.TestCase):

    def setUp(self):
        self.analysis = Analysis()
        self.analysis.analysis_name = "test"
        self.analysis.source_directory = "/path/to/source"
        self.result_relative_analysis_path = "source/dir1"

    def tearDown(self):
        pass

    def test_create_relative_analysis_path_from_filepath(self):
        """Test creating a relative analysis path from a fill file path."""

        full_file_path = f'{self.analysis.source_directory}/dir1/file.js'
        expected_relative_analysis_path = "source/dir1/file.js"
        relative_analysis_path = ParsingMixin.create_relative_analysis_file_path(self.analysis.source_directory, full_file_path)
        self.assertTrue(relative_analysis_path == expected_relative_analysis_path)

    def test_create_relative_analysis_path_for_dependency(self):
        """Test creating a relative analysis path for a dependency name."""

        dependency = 'file1.js'
        expected_relative_analysis_dependency_path = f"{self.result_relative_analysis_path}/{dependency}"
        relative_analysis_dependency_path = ParsingMixin.create_relative_analysis_path_for_dependency(dependency, self.result_relative_analysis_path)
        self.assertTrue(relative_analysis_dependency_path == expected_relative_analysis_dependency_path)

    def test_resolve_relative_dependency_path(self):
        """Test resolving a relative analysis path of a dependency."""

        file_name = "file1.js"
        full_file_path = "source/dir1/file.js"

        dependency1_before_resolve = '../dir2/dependency1.js'
        expected_resolved_dependency1_path = 'source/dir2/dependency1.js'

        dependency2_before_resolve = '../dependency2.js'
        expected_resolved_dependency2_path = 'source/dependency2.js'

        relative_file_path_to_analysis = ParsingMixin.create_relative_analysis_file_path(self.analysis.source_directory, full_file_path)

        file_result = FileResult.create_file_result(
            analysis=self.analysis,
            scanned_file_name=file_name,
            relative_file_path_to_analysis=relative_file_path_to_analysis,
            absolute_name=full_file_path,
            display_name=relative_file_path_to_analysis,
            module_name="",
            scanned_by="parser_name",
            scanned_language=LanguageType.JAVASCRIPT,
            scanned_tokens="token1 token2",
            preprocessed_source=""
        )

        resolved_dependency1 = ParsingMixin.resolve_relative_dependency_path(
            dependency1_before_resolve,
            file_result.absolute_dir_path,
            self.analysis.source_directory
        )

        self.assertTrue(resolved_dependency1 == expected_resolved_dependency1_path)

        resolved_dependency2 = ParsingMixin.resolve_relative_dependency_path(
            dependency2_before_resolve,
            file_result.absolute_dir_path,
            self.analysis.source_directory
        )
        
        self.assertTrue(resolved_dependency2 == expected_resolved_dependency2_path)
