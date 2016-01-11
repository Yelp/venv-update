from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import platform
from os import environ

import pytest


TRAVIS_PYTHON_VERSION = 'TRAVIS_PYTHON_VERSION'
PYPY = 'PyPy'


@pytest.fixture
def fixed_environment_variables():
    # don't clear environment variables.
    pass


@pytest.mark.skipif(TRAVIS_PYTHON_VERSION not in environ, reason='$TRAVIS_PYTHON_VERSION not set')
def test_travis_python_environment():
    travis_python_version = environ[TRAVIS_PYTHON_VERSION]

    travis_python_version = travis_python_version.lower()
    if travis_python_version == 'pypy':
        assert platform.python_implementation() == PYPY
        expected_version = (2, 7)
    elif travis_python_version == 'pypy3':
        assert platform.python_implementation() == PYPY
        expected_version = (3, 2)
    else:
        expected_version = tuple([int(part) for part in travis_python_version.split('.')])

    from sys import version_info
    assert expected_version == version_info[:2]
