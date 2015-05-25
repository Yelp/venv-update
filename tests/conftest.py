from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import pytest
import shutil
import subprocess
import sys
import tempfile
import time
import socket
from errno import ECONNREFUSED

import six


@pytest.fixture(scope='session', autouse=True)
def no_pip_environment_vars():
    for var in dict(os.environ):
        if var.startswith('PIP_'):
            del os.environ[var]


@pytest.fixture(scope='session', autouse=True)
def no_pythonpath_environment_var():
    for var in dict(os.environ):
        if var == 'PYTHONPATH':
            del os.environ[var]


@pytest.yield_fixture(scope='session', autouse=True)
def pypi_server():
    # Need to use tempfile.mkdtemp because we're session scoped
    # (otherwise I'd use the `tmpdir` fixture)
    tmpdir = tempfile.mkdtemp()
    for package in os.listdir('tests/testing/packages'):
        pkg_dir = os.path.join(tmpdir, package)
        os.makedirs(pkg_dir)
        subprocess.check_call(
            (sys.executable, 'setup.py', 'sdist', '--dist-dir', pkg_dir),
            cwd='tests/testing/packages/' + package,
        )

    port = 9001
    proc = subprocess.Popen(
        (sys.executable, '-m', six.moves.SimpleHTTPServer.__name__, str(port)),
        cwd=tmpdir,
    )

    while not service_up(port):
        time.sleep(.1)

    try:
        yield
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(tmpdir)


def service_up(port):
    try:
        return six.moves.urllib.request.urlopen(
            'http://localhost:{0}'.format(port)
        ).getcode() == 200
    except IOError as error:
        if isinstance(error.errno, int):
            errno = error.errno
        # urllib throws an IOError with a string in the errno slot -.-
        elif len(error.args) > 1 and isinstance(error.args[1], socket.error):
            errno = error.args[1].errno
        elif len(error.args) == 1 and isinstance(error.args[0], socket.error):
            errno = error.args[0].errno
        else:
            raise ValueError("Could not find error number: %r" % error)

        if errno == ECONNREFUSED:
            return False
        else:
            raise
