from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import socket
import subprocess
import sys
import time
from errno import ECONNREFUSED

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


@pytest.yield_fixture(scope='session')
def pypi_fallback():
    """should we fall back to the global python.org servers?"""
    yield True


@pytest.yield_fixture(scope='session')
def pypi_server(pypi_fallback):
    packages = 'build/packages'
    subprocess.check_call(
        (
            sys.executable,
            'tests/testing/make_sdists.py',
            'tests/testing/packages',
            '.',  # we need pip-faster too be installable too
            packages,
        ),
        cwd=str(TOP),
    )

    port = str(reserve())
    cmd = ('pypi-server', '-i', '127.0.0.1', '-p', port)
    if not pypi_fallback:
        cmd += ('--disable-fallback',)
    cmd += (packages,)
    print(colorize(cmd))
    server = subprocess.Popen(cmd, close_fds=True, cwd=str(TOP))
    os.environ['PIP_INDEX_URL'] = 'http://localhost:' + port + '/simple'

    limit = 10
    poll = .1
    while True:
        if server.poll() is not None:
            raise AssertionError('pypi ended! (code %i)' % server.returncode)
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
        server.terminate()
        server.wait()


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
