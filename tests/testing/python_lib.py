#!/usr/bin/env python
from __future__ import print_function

from distutils.sysconfig import get_python_lib
import os
import sys

PYTHON_LIB = os.path.relpath(get_python_lib(), sys.prefix)

if __name__ == '__main__':
    print(PYTHON_LIB)
