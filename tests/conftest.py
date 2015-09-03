from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest


@pytest.fixture(scope='session', autouse=True)
def no_pip_environment_vars():
    import os
    for var in dict(os.environ):
        if var.startswith('PIP_'):
            del os.environ[var]


@pytest.fixture(scope='session', autouse=True)
def no_pythonpath_environment_var():
    import os
    for var in dict(os.environ):
        if var == 'PYTHONPATH':
            del os.environ[var]
