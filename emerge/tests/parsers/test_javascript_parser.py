"""
All unit tests that are related to JavaScriptParser.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict
import unittest

from tests.testdata.javascript import JAVASCRIPT_TEST_FILES, JAVASCRIPT_ENTITY_TEST_FILES

from emerge.languages.javascriptparser import JavaScriptParser
from emerge.results import FileResult, EntityResult
from emerge.languages.abstractparser import LanguageType
from emerge.analysis import Analysis


class JavaScriptParserTestCase(unittest.TestCase):

    def setUp(self):
        self.example_data = JAVASCRIPT_TEST_FILES
        self.parser = JavaScriptParser()
        self.analysis = Analysis()
        self.analysis.analysis_name = "test"
        self.analysis.source_directory = "/tests"

    def tearDown(self):
        pass

    def test_generate_file_results(self):
        """Generate file results for all parsers and check if metrics were calculated."""
        self.assertFalse(self.parser.results)

        for file_name, file_content in self.example_data.items():
            self.parser.generate_file_result_from_analysis(self.analysis, file_name=file_name, full_file_path="/tests/" + file_name, file_content=file_content)

        results: Dict[str, FileResult] = self.parser.results
        self.assertTrue(results)
        self.assertTrue(len(results) == 4)

        result: FileResult
        for _, result in results.items():
            self.assertTrue(len(result.scanned_tokens) > 0)
            self.assertTrue(len(result.scanned_import_dependencies) > 0)

            self.assertTrue(result.analysis.analysis_name.strip())
            self.assertTrue(result.scanned_file_name.strip())
            self.assertTrue(result.scanned_by.strip())
            self.assertTrue(result.scanned_language == LanguageType.JAVASCRIPT)

    def test_generate_entity_results(self):
        """Generate entity results for JavaScript ES6 classes and check their basic attributes and inheritance."""
        self.assertFalse(self.parser.results)

        for file_name, file_content in JAVASCRIPT_ENTITY_TEST_FILES.items():
            self.parser.generate_file_result_from_analysis(self.analysis, file_name=file_name, full_file_path="/tests/" + file_name, file_content=file_content)

        self.parser.generate_entity_results_from_analysis(self.analysis)
        self.analysis.collect_results_from_parser(self.parser)
        entity_results = self.analysis.entity_results

        self.assertTrue(entity_results)
        self.assertTrue(len(entity_results) == 3)

        entity_names = {result.entity_name for result in entity_results.values()}
        self.assertTrue(entity_names == {"Animal", "Dog", "Cat"})

        result: EntityResult
        for _, result in entity_results.items():
            self.assertTrue(len(result.scanned_tokens) > 0)
            self.assertTrue(result.analysis.analysis_name.strip())
            self.assertTrue(result.entity_name.strip())
            self.assertTrue(result.scanned_file_name.strip())
            self.assertTrue(result.scanned_by.strip())
            self.assertTrue(result.scanned_language == LanguageType.JAVASCRIPT)

        # inheritance dependencies should have been extracted from the 'extends' clauses
        inheritance = {result.entity_name: result.scanned_inheritance_dependencies for result in entity_results.values()}
        self.assertTrue("EventEmitter" in inheritance["Animal"])
        self.assertTrue("Animal" in inheritance["Dog"])
        self.assertTrue("Animal" in inheritance["Cat"])
