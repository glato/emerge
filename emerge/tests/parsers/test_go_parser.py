"""
All unit tests that are related to GoParser.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import unittest
from typing import Dict

from tests.testdata.go import GO_TEST_FILES

from emerge.graph import GraphType
from emerge.languages.goparser import GoParser
from emerge.results import FileResult
from emerge.languages.abstractparser import LanguageType
from emerge.analysis import Analysis


class GoParserTestCase(unittest.TestCase):

    def setUp(self):
        self.example_data = GO_TEST_FILES
        self.parser = GoParser()
        self.analysis = Analysis()
        self.analysis.analysis_name = "test"
        self.analysis.source_directory = "/tests"

    def tearDown(self):
        pass

    def test_generate_file_results(self):
        """Generate file results and check basic attributes."""
        self.assertFalse(self.parser.results)

        # we need to have a filesystem graph before trying to extract any import dependencies fo golang
        self.analysis.create_graph_representation(GraphType.FILESYSTEM_GRAPH)
        self.analysis.create_filesystem_graph()

        for file_name, file_content in self.example_data.items():
            self.parser.generate_file_result_from_analysis(self.analysis, file_name=file_name, full_file_path="/tests/" + file_name, file_content=file_content)
            self.parser.after_generated_file_results(self.analysis)

        results: Dict[str, FileResult] = self.parser.results
        self.assertTrue(results)
        self.assertTrue(len(results) == 2)

        result: FileResult
        for _, result in results.items():
            self.assertTrue(len(result.scanned_tokens) > 0)
            self.assertTrue(len(result.scanned_import_dependencies) > 0)
            self.assertTrue(all(isinstance(dependency, str) for dependency in result.scanned_import_dependencies))
            self.assertTrue(result.analysis.analysis_name.strip())
            self.assertTrue(result.scanned_file_name.strip())
            self.assertTrue(result.scanned_by.strip())
            self.assertTrue(result.scanned_language == LanguageType.GO)
