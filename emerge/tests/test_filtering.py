"""
All unit tests that are related to filtering functionality.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import unittest
from emerge.config import Configuration
from emerge.analysis import Analysis
import coloredlogs
import logging

LOGGER = logging.getLogger('TESTS')
coloredlogs.install(level='INFO', logger=LOGGER, fmt='\n%(asctime)s %(name)s %(levelname)s %(message)s')


# pylint: disable=protected-access
class FilteringTestCase(unittest.TestCase):

    def setUp(self):
        self.version = "1.0.0"
        self.configuration = Configuration(self.version)
        self.analysis = Analysis()

    def tearDown(self):
        pass

    def test_file_inclusions_exact_files(self):
        """Test exact file inclusions filter"""
        self.analysis.file_inclusions = {
            'exact_files': ['test.py', 'main.py']
        }

        # Should include these files
        self.assertTrue(self.analysis.should_include_file('src/test.py'))
        self.assertTrue(self.analysis.should_include_file('src/main.py'))

        # Should exclude these files
        self.assertFalse(self.analysis.should_include_file('src/other.py'))
        self.assertFalse(self.analysis.should_include_file('src/utils.py'))

        LOGGER.info('completed testing of file inclusions with exact files')

    def test_file_inclusions_patterns(self):
        """Test pattern-based file inclusions"""
        self.analysis.file_inclusions = {
            'patterns': ['*_manager.py', 'test_*.py']
        }

        # Should include these files
        self.assertTrue(self.analysis.should_include_file('src/state_manager.py'))
        self.assertTrue(self.analysis.should_include_file('src/git_manager.py'))
        self.assertTrue(self.analysis.should_include_file('tests/test_config.py'))

        # Should exclude these files
        self.assertFalse(self.analysis.should_include_file('src/models.py'))
        self.assertFalse(self.analysis.should_include_file('src/utils.py'))

        LOGGER.info('completed testing of file inclusions with patterns')

    def test_file_inclusions_directories(self):
        """Test directory-based file inclusions"""
        self.analysis.file_inclusions = {
            'directories': ['src/core/', 'src/models/']
        }

        # Should include these files
        self.assertTrue(self.analysis.should_include_file('src/core/main.py'))
        self.assertTrue(self.analysis.should_include_file('src/models/user.py'))

        # Should exclude these files
        self.assertFalse(self.analysis.should_include_file('src/utils.py'))
        self.assertFalse(self.analysis.should_include_file('tests/test.py'))

        LOGGER.info('completed testing of file inclusions with directories')

    def test_file_exclusions_exact_files(self):
        """Test exact file exclusions filter"""
        self.analysis.file_exclusions = {
            'exact_files': ['__init__.py', 'setup.py']
        }

        # Should exclude these files
        self.assertTrue(self.analysis.should_exclude_file('src/__init__.py', '__init__.py'))
        self.assertTrue(self.analysis.should_exclude_file('setup.py', 'setup.py'))

        # Should not exclude these files
        self.assertFalse(self.analysis.should_exclude_file('src/main.py', 'main.py'))
        self.assertFalse(self.analysis.should_exclude_file('src/models.py', 'models.py'))

        LOGGER.info('completed testing of file exclusions with exact files')

    def test_file_exclusions_patterns(self):
        """Test pattern-based file exclusions"""
        self.analysis.file_exclusions = {
            'patterns': ['test_*.py', '*_test.py', '*.pyc']
        }

        # Should exclude these files
        self.assertTrue(self.analysis.should_exclude_file('tests/test_config.py', 'test_config.py'))
        self.assertTrue(self.analysis.should_exclude_file('src/models_test.py', 'models_test.py'))
        self.assertTrue(self.analysis.should_exclude_file('src/main.pyc', 'main.pyc'))

        # Should not exclude these files
        self.assertFalse(self.analysis.should_exclude_file('src/models.py', 'models.py'))
        self.assertFalse(self.analysis.should_exclude_file('src/config.py', 'config.py'))

        LOGGER.info('completed testing of file exclusions with patterns')

    def test_file_exclusions_directories(self):
        """Test directory-based file exclusions"""
        self.analysis.file_exclusions = {
            'directories': ['tests/', 'build/', '__pycache__/']
        }

        # Should exclude these directories
        self.assertTrue(self.analysis.should_exclude_directory('tests/', 'tests'))
        self.assertTrue(self.analysis.should_exclude_directory('build/output', 'output'))
        self.assertTrue(self.analysis.should_exclude_directory('src/__pycache__', '__pycache__'))

        # Should not exclude these directories
        self.assertFalse(self.analysis.should_exclude_directory('src/', 'src'))
        self.assertFalse(self.analysis.should_exclude_directory('lib/', 'lib'))

        LOGGER.info('completed testing of directory exclusions')

    def test_combined_inclusions_and_exclusions(self):
        """Test combined inclusions and exclusions"""
        self.analysis.file_inclusions = {
            'directories': ['src/']
        }
        self.analysis.file_exclusions = {
            'patterns': ['test_*.py']
        }

        # Should include (in src/) and not excluded
        self.assertTrue(self.analysis.should_include_file('src/models.py'))
        self.assertFalse(self.analysis.should_exclude_file('src/models.py', 'models.py'))

        # Should not include (not in src/)
        self.assertFalse(self.analysis.should_include_file('lib/utils.py'))

        # Should include but then be excluded (test file)
        self.assertTrue(self.analysis.should_include_file('src/test_models.py'))
        self.assertTrue(self.analysis.should_exclude_file('src/test_models.py', 'test_models.py'))

        LOGGER.info('completed testing of combined inclusions and exclusions')

    def test_no_filters_includes_all(self):
        """Test that when no filters are specified, all files are included"""
        # No filters set
        self.analysis.file_inclusions = None
        self.analysis.file_exclusions = None

        # Should include all files
        self.assertTrue(self.analysis.should_include_file('any/file.py'))
        self.assertTrue(self.analysis.should_include_file('test_file.py'))
        self.assertFalse(self.analysis.should_exclude_file('any/file.py', 'file.py'))

        LOGGER.info('completed testing of no filters behavior')

    def test_filter_profile_parsing(self):
        """Test filter profile parsing in configuration"""
        self.configuration.filter_profiles = {
            'test-profile': {
                'profile_name': 'test-profile',
                'file_inclusions': {
                    'exact_files': ['main.py', 'config.py']
                },
                'file_exclusions': {
                    'patterns': ['test_*.py']
                },
                'metric_filters': {
                    'min_sloc': 50,
                    'max_sloc': 500
                }
            }
        }

        self.assertIn('test-profile', self.configuration.filter_profiles)
        profile = self.configuration.filter_profiles['test-profile']
        self.assertEqual(profile['profile_name'], 'test-profile')
        self.assertIn('file_inclusions', profile)
        self.assertIn('file_exclusions', profile)
        self.assertIn('metric_filters', profile)

        LOGGER.info('completed testing of filter profile parsing')

    def test_metric_filters_structure(self):
        """Test metric filters structure"""
        self.analysis.metric_filters = {
            'min_sloc': 50,
            'max_sloc': 500,
            'min_fan_out': 5,
            'max_fan_in': 20
        }

        self.assertEqual(self.analysis.metric_filters['min_sloc'], 50)
        self.assertEqual(self.analysis.metric_filters['max_sloc'], 500)
        self.assertEqual(self.analysis.metric_filters['min_fan_out'], 5)
        self.assertEqual(self.analysis.metric_filters['max_fan_in'], 20)

        LOGGER.info('completed testing of metric filters structure')


if __name__ == '__main__':
    unittest.main()
