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
    assert err == ''
    out = uncolor(out)
    assert out.endswith('''
tracing: circular-dep-a
already queued: circular-dep-b==1.0 (from circular-dep-a)
tracing: circular-dep-b==1.0 (from circular-dep-a)
Circular dependency! circular-dep-a==1.0 (from circular-dep-b==1.0->circular-dep-a)
''')

    frozen_requirements = pip_freeze(str(venv)).split('\n')
    assert 'circular-dep-a==1.0' in frozen_requirements
    assert 'circular-dep-b==1.0' in frozen_requirements


@pytest.mark.usefixtures('pypi_server')
@pytest.mark.skipif(
    sys.version_info > (3, 0),
    reason='ancient versions are not py3 compatible, even for install',
)
@pytest.mark.parametrize('reqs', [
    # old setuptools and old pip
    ['setuptools==0.6c11', 'pip==1.4.1'],
    # old setuptools and new pip
    ['setuptools==0.6c11', 'pip==1.5.6'],
    # new setuptools and old pip
    ['setuptools==18.2', 'pip==1.4.1'],
])
def test_old_pip_and_setuptools(tmpdir, reqs):
    """We should be able to use pip-faster's wheel building even if we have
    ancient pip and setuptools.

    https://github.com/Yelp/venv-update/issues/33
    """
    tmpdir.chdir()

    # 1. Create an empty virtualenv.
    # 2. Install old pip/setuptools that don't support wheel building.
    # 3. Install pip-faster.
    # 4. Install pure-python-package and assert it was wheeled during install.
    tmpdir.join('venv')
    venv = Path('venv')
    run('virtualenv', venv.strpath)

    # We need to add public PyPI as an extra URL since we're installing
    # packages (setuptools and pip) which aren't available from our PyPI fixture.
    from os import environ
    environ['PIP_EXTRA_INDEX_URL'] = 'https://pypi.python.org/simple/'
    try:
        pip = venv.join('bin/pip').strpath
        for req in reqs:
            run(pip, 'install', '--', req)
        # wheel needs argparse but it won't get installed
        if sys.version_info < (2, 7):
            run(pip, 'install', 'argparse')
        run(pip, 'install', 'venv-update==' + __version__)
    finally:
        del environ['PIP_EXTRA_INDEX_URL']

    run(str(venv.join('bin/pip-faster')), 'install', 'pure_python_package')

    # it was installed
    assert 'pure-python-package==0.2.0' in pip_freeze(str(venv)).split('\n')

    # it was wheeled
    from pip.wheel import Wheel
    wheelhouse = tmpdir.join('home', '.cache', 'pip-faster', 'wheelhouse')
    assert 'pure-python-package' in [
        Wheel(f.basename).name for f in wheelhouse.listdir()
    ]


@pytest.mark.usefixtures('tmpdir')
def test_install_whl_over_http(pypi_server):
    whl_url = pypi_server + '/packages/wheeled_package-0.2.0-py2.py3-none-any.whl'
    venv = make_venv()

    out, err = run(str(venv.join('bin/pip-faster')), 'install', whl_url)
    assert err == ''
    out = uncolor(out)
    assert out == '''\
Downloading/unpacking %s/packages/wheeled_package-0.2.0-py2.py3-none-any.whl
  Downloading wheeled_package-0.2.0-py2.py3-none-any.whl
  Saved ./home/.cache/pip-faster/wheelhouse/wheeled_package-0.2.0-py2.py3-none-any.whl
Installing collected packages: wheeled-package
Successfully installed wheeled-package
Cleaning up...
''' % pypi_server
