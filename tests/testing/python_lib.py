#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
from distutils.sysconfig import get_python_lib  # pylint:disable=import-error

PYTHON_LIB = os.path.relpath(get_python_lib(), sys.prefix)
