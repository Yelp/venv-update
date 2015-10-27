from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import socket
import subprocess
import sys
import tempfile
import time
from errno import ECONNREFUSED

import py.path  # pylint:disable=import-error
import pytest
import six
from testing import TOP
from testing.ephemeral_port_reserve import reserve

from venv_update import colorize


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
    packages = py.path.local(tempfile.mkdtemp('packages'))
    orig_packages = TOP.join('tests/testing/packages')

    # setuptools explodes if you try to run multiple instances simultaneously
    # in the same directory, so we need to make a copy for each thread.
    orig_packages.copy(packages)
    for package in packages.listdir():
        with package.as_cwd():
            subprocess.check_call((sys.executable, 'setup.py', 'sdist'))

    # We want pip-faster to be installable too, so copy it into the fixtured packages directory as well.
    tmp_top = py.path.local(tempfile.mktemp('pip-faster'))
    TOP.copy(tmp_top)
    subprocess.check_call(
        (sys.executable, str(tmp_top / 'setup.py'), 'sdist', '--dist-dir', str(packages / 'pip-faster')),
        cwd=str(tmp_top),
    )

    port = str(reserve())
    cmd = ('pypi-server', '-i', '127.0.0.1', '-p', port, packages.strpath)
    print(colorize(cmd))
    proc = subprocess.Popen(cmd, close_fds=True)
    os.environ['PIP_INDEX_URL'] = 'http://localhost:' + port + '/simple'

    limit = 10
    poll = .1
    while True:
        if proc.poll() is not None:
            raise AssertionError('pypi ended! (code %i)' % proc.returncode)
        elif service_up(port):
            break
        elif limit > 0:
            time.sleep(poll)
            limit -= poll
        else:
            raise AssertionError('pypi server never became ready!')

    try:
        yield
    finally:
        proc.terminate()
        proc.wait()
        packages.remove()
        tmp_top.remove()


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
            raise ValueError('Could not find error number: %r' % error)

        if errno == ECONNREFUSED:
            return False
        else:
            raise
