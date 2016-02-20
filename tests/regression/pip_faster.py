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


@pytest.mark.usefixtures('pypi_server')
def test_circular_dependencies(tmpdir):
    """pip-faster should be able to install packages with circular
    dependencies."""
    tmpdir.chdir()
    enable_coverage()
    venv = Path('venv')
    run('virtualenv', venv.strpath)
    install_coverage(venv.strpath)

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster==' + __version__)

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
adding sub-requirement circular-dep-b==1.0 (from circular-dep-a)
tracing: circular-dep-b==1.0 (from circular-dep-a)
adding sub-requirement circular-dep-a==1.0 (from circular-dep-b==1.0->circular-dep-a)
already analyzed: circular-dep-b==1.0 (from circular-dep-a)
tracing: circular-dep-a==1.0 (from circular-dep-b==1.0->circular-dep-a)
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

    https://github.com/Yelp/pip-faster/issues/33
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
        run(pip, 'install', 'pip-faster==' + __version__)
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
