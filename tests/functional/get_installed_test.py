from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from testing import run
from venv_update import __version__

ALWAYS = set(['pip', 'venv-update', 'setuptools', 'wheel'])


def get_installed():
    out, err = run('myvenv/bin/python', '-c', '''\
import pip_faster as p
for p in sorted(p.reqnames(p.pip_get_installed())):
    print(p)''')

    assert err == ''
    out = set(out.split())

    # Most python distributions which have argparse in the stdlib fail to
    # expose it to setuptools as an installed package (it seems all but ubuntu
    # do this). This results in argparse sometimes being installed locally,
    # sometimes not, even for a specific version of python.
    # We normalize by never looking at argparse =/
    out -= set(['argparse'])

    # these will always be present
    assert ALWAYS.issubset(out)
    return sorted(out - ALWAYS)


@pytest.mark.usefixtures('pypi_server_with_fallback')
def test_pip_get_installed(tmpdir):
    tmpdir.chdir()

    run('virtualenv', 'myvenv')
    run('rm', '-rf', 'myvenv/local')
    run('myvenv/bin/pip', 'install', 'venv-update==' + __version__)

    assert get_installed() == []

    run(
        'myvenv/bin/pip', 'install',
        'hg+https://bitbucket.org/bukzor/coverage.py@__main__-support#egg=coverage',
        'git+git://github.com/bukzor/cov-core.git@master#egg=cov-core',
        '-e', 'git+git://github.com/bukzor/pytest-cov.git@master#egg=pytest-cov',
    )
    assert get_installed() == ['cov-core', 'coverage', 'py', 'pytest', 'pytest-cov']

    run('myvenv/bin/pip', 'uninstall', '--yes', 'cov-core', 'coverage', 'py', 'pytest', 'pytest-cov')
    assert get_installed() == []

    run('myvenv/bin/pip', 'install', 'flake8')
    assert get_installed() == ['flake8', 'mccabe', 'pep8', 'pyflakes']

    run('myvenv/bin/pip', 'uninstall', '--yes', 'flake8')
    assert get_installed() == ['mccabe', 'pep8', 'pyflakes']
