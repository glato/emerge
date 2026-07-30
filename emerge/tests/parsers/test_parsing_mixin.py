"""
All unit tests that are related to the ParsingMixin.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import unittest

from emerge.results import FileResult
from emerge.analysis import Analysis
from emerge.languages.abstractparser import LanguageType, ParsingMixin, ReadAheadWordList


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
            source="",
            preprocessed_source="",
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

    def test_gen_word_read_ahead_yields_correct_tail(self):
        """Each read-ahead should expose exactly the tokens that follow the current one."""

        list_of_words = ["import", "foo", "from", "'bar'", ";", "class", "Baz", "{", "}"]

        for index, obj, following in ParsingMixin._gen_word_read_ahead(list_of_words):
            self.assertTrue(obj == list_of_words[index])
            # the read-ahead must equal the classic slice of the remaining tokens
            self.assertTrue(list(following) == list_of_words[index + 1:])

        # the last token has no successors, so its read-ahead must be empty
        *_, (last_index, _, last_following) = ParsingMixin._gen_word_read_ahead(list_of_words)
        self.assertTrue(last_index == len(list_of_words) - 1)
        self.assertTrue(len(last_following) == 0)

    def test_gen_word_read_ahead_supports_slicing_and_concatenation(self):
        """The read-ahead view must behave like a list for the operations the parsers rely on."""

        list_of_words = ["class", "Foo", "extends", "Bar", "{", "}"]

        _, obj, following = next(ParsingMixin._gen_word_read_ahead(list_of_words))

        # slicing (used e.g. for the debug read-ahead) returns a plain list
        self.assertTrue(following[:2] == ["Foo", "extends"])
        # 'list + following' concatenation is used across the parsers
        self.assertTrue([obj] + following[:2] == ["class", "Foo", "extends"])
        self.assertTrue([obj] + following == list_of_words)
        # indexing and length
        self.assertTrue(following[0] == "Foo")
        self.assertTrue(len(following) == len(list_of_words) - 1)
        # create_read_ahead_string joins the current token with all following tokens
        self.assertTrue(ParsingMixin.create_read_ahead_string(obj, following) == " ".join(list_of_words))

    def test_gen_word_read_ahead_is_a_lazy_view(self):
        """The read-ahead must be a lightweight view over the original list, not a per-token copy."""

        list_of_words = ["a", "b", "c", "d"]

        views = [following for _, _, following in ParsingMixin._gen_word_read_ahead(list_of_words)]
        self.assertTrue(all(isinstance(view, ReadAheadWordList) for view in views))
        # a view holds a reference to the original list instead of copying its tail
        self.assertTrue(all(view._data is list_of_words for view in views))
