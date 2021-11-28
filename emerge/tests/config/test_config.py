"""
All unit tests that are related to configuration.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import unittest
from emerge.config import Configuration
from emerge.config import Analysis, YamlLoader
import coloredlogs
import logging

LOGGER = logging.getLogger('TESTS')
coloredlogs.install(level='INFO', logger=LOGGER, fmt='\n%(asctime)s %(name)s %(levelname)s %(message)s')


# pylint: disable=protected-access
class ConfigurationTestCase(unittest.TestCase):

    def setUp(self):
        self.version = "1.0.0"
        self.configuration = Configuration(self.version)
        self.analysis = Analysis()

    def tearDown(self):
        pass

    def test_config_init(self):
        self.assertIsNotNone(self.configuration)
        self.assertIsNotNone(self.configuration.analyses)
        self.assertTrue(len(self.configuration.analyses) == 0)
        self.assertTrue(self.configuration.project_name == "unnamed")
        self.assertIsNotNone(self.configuration._yaml_loader)
        self.assertIs(type(self.configuration._yaml_loader), YamlLoader)
        LOGGER.info(f'completed testing of CurrentConfiguration init')


if __name__ == '__main__':
    unittest.main()
