"""
Discover and run all unit tests.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import unittest

loader = unittest.TestLoader()
start_dir = '.'
suite = loader.discover(start_dir)

runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
