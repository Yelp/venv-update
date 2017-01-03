from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys

import pytest

from testing import enable_coverage
from testing import install_coverage
from testing import Path
from testing import pip_freeze
from testing import run
from testing import uncolor
from venv_update import __version__


def make_venv():
    enable_coverage()
    venv = Path('venv')
    run('virtualenv', venv.strpath)
    install_coverage(venv.strpath)

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'venv-update==' + __version__)
    return venv


@pytest.mark.usefixtures('pypi_server', 'tmpdir')
def test_circular_dependencies():
    """pip-faster should be able to install packages with circular
    dependencies."""
    venv = make_venv()

    out, err = run(
        venv.join('bin/pip-faster').strpath,
        'install',
        '-vv',  # show debug logging
        'circular-dep-a',
    )
    assert err == 'Circular dependency! circular-dep-a==1.0 (from circular-dep-b==1.0->circular-dep-a)\n'
    out = uncolor(out)
    assert out.endswith('''
tracing: circular-dep-a
already queued: circular-dep-b==1.0 (from circular-dep-a)
tracing: circular-dep-b==1.0 (from circular-dep-a)
''')

    frozen_requirements = pip_freeze(str(venv)).split('\n')
    assert 'circular-dep-a==1.0' in frozen_requirements
    assert 'circular-dep-b==1.0' in frozen_requirements


@pytest.mark.usefixtures('tmpdir')
def test_install_whl_over_http(pypi_server):
    whl_url = pypi_server + '/packages/wheeled_package-0.2.0-py2.py3-none-any.whl'
    venv = make_venv()

    out, err = run(str(venv.join('bin/pip-faster')), 'install', whl_url)
    assert err == ''
    out = uncolor(out)
    assert out == '''\
Collecting wheeled-package==0.2.0 from {pypi_server}/packages/wheeled_package-0.2.0-py2.py3-none-any.whl
  Downloading {pypi_server}/packages/wheeled_package-0.2.0-py2.py3-none-any.whl
  Saved ./home/.cache/pip-faster/wheelhouse/wheeled_package-0.2.0-py2.py3-none-any.whl
Skipping wheeled-package, due to already being wheel.
Installing collected packages: wheeled-package
Successfully installed wheeled-package-0.2.0
'''.format(pypi_server=pypi_server)
