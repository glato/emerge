"""
Allow emerge to be importable by a start script (e.g. installed by pip) as a standalone tool.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from emerge.appear import Emerge


def run():
    emerge = Emerge()
    emerge.start()


if __name__ == "__main__":
    run()
