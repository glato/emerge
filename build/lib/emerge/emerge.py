"""
Simple wrapper to start emerge as a standalone tool.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

import core.appear


def run():
    emerge = core.appear.Emerge()
    emerge.start()


if __name__ == "__main__":
    run()
