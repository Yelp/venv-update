from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import platform
from os import environ

import pytest

PYPY = 'PyPy'


@pytest.fixture
def fixed_environment_variables():
    # don't clear environment variables.
    pass


@pytest.mark.skipif('PYTHON' not in environ, reason='$PYTHON not set')
def test_python_version():
    python_version = environ['PYTHON'].lower()
    if python_version == 'pypy':  # :pragma:nocover: coverage under pypy is too slow.
        assert platform.python_implementation() == PYPY
        expected_version = (2, 7)
    elif python_version == 'pypy3':  # :pragma:nocover: coverage under pypy is too slow.
        assert platform.python_implementation() == PYPY
        expected_version = (3, 2)
    else:  # eg python3.4
        expected_version = python_version.replace('python', '').split('.')
        expected_version = tuple(int(part) for part in expected_version)

    from sys import version_info
    assert expected_version == version_info[:2]
