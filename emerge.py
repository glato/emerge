# -*- coding: utf-8 -*-

import re
import sys
from emerge.main import run  # pylint: disable=no-name-in-module

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(run())
