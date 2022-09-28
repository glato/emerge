"""
All unit tests that are related to KotlinParser.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict
import unittest

from tests.testdata.kotlin import KOTLIN_TEST_FILES

from emerge.languages.kotlinparser import KotlinParser
from emerge.results import FileResult, EntityResult
from emerge.languages.abstractparser import LanguageType
from emerge.analysis import Analysis


class KotlinParserTestCase(unittest.TestCase):

    def setUp(self):
        self.example_data = KOTLIN_TEST_FILES
        self.parser = KotlinParser()
        self.analysis = Analysis()
        self.analysis.analysis_name = "test"
        self.analysis.source_directory = "/tests"

    def tearDown(self):
        pass

    def test_generate_file_results(self):
        """Generate file results and check basic attributes."""
        self.assertFalse(self.parser.results)

        for file_name, file_content in self.example_data.items():
            self.parser.generate_file_result_from_analysis(self.analysis, file_name=file_name, full_file_path="/tests/" + file_name, file_content=file_content)

        results: Dict[str, FileResult] = self.parser.results
        self.assertTrue(results)
        self.assertTrue(len(results) == 2)

        result: FileResult
        for _, result in results.items():
            self.assertTrue(len(result.scanned_tokens) > 0)
            self.assertTrue(len(result.scanned_import_dependencies) > 0)

            self.assertTrue(result.analysis.analysis_name.strip())
            self.assertTrue(result.scanned_file_name.strip())
            self.assertTrue(result.scanned_by.strip())
            self.assertTrue(result.scanned_language == LanguageType.KOTLIN)

    def test_generate_entity_results(self):
        """Generate entity results and check basic attributes."""
        self.assertFalse(self.parser.results)

        for file_name, file_content in self.example_data.items():
            self.parser.generate_file_result_from_analysis(self.analysis, file_name=file_name, full_file_path="/tests/" + file_name, file_content=file_content)

        results: Dict[str, EntityResult] = self.parser.results
        self.assertTrue(results)
        self.assertTrue(len(results) == 2)

        self.parser.generate_entity_results_from_analysis(self.analysis)
        self.analysis.collect_results_from_parser(self.parser)
        entity_results = self.analysis.entity_results

        self.assertTrue(len(entity_results) == 2)

        result: EntityResult
        for _, result in entity_results.items():
            self.assertTrue(len(result.scanned_tokens) > 0)
            self.assertTrue(len(result.scanned_import_dependencies) > 0)
            self.assertTrue(result.analysis.analysis_name.strip())
            self.assertTrue(result.entity_name.strip())
            self.assertTrue(result.scanned_file_name.strip())
            self.assertTrue(result.scanned_by.strip())
            self.assertTrue(result.scanned_language == LanguageType.KOTLIN)
