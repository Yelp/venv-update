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


@pytest.mark.skipif('TOXENV' not in environ, reason='$TOXENV not set')
def test_python_version():
    python_version = environ['TOXENV'].lower()
    if python_version == 'pypy':  # :pragma:nocover: coverage under pypy is too slow.
        assert platform.python_implementation() == PYPY
        expected_version = (2, 7)
    elif python_version == 'pypy3':  # :pragma:nocover: coverage under pypy is too slow.
        assert platform.python_implementation() == PYPY
        expected_version = (3, 2)
    else:  # eg py34
        major, minor = python_version[2:4]
        expected_version = (int(major), int(minor))

    from sys import version_info
    assert expected_version == version_info[:2]
