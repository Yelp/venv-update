from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from testing import enable_coverage
from testing import pip_freeze
from testing import requirements
from testing import run
from testing import TOP
from venv_update import __version__


def it_shows_help_for_prune():
    out, err = run('pip-faster', 'install', '--help')
    assert '''
  --no-clean                  Don't clean up build directories.
  --prune                     Uninstall any non-required packages.
  --no-prune                  Do not uninstall any non-required packages.

Package Index Options:
''' in out
    assert err == ''


@pytest.mark.usefixtures('pypi_server')
def it_installs_stuff(tmpdir):
    venv = tmpdir.join('venv')
    run('virtualenv', str(venv))

    assert pip_freeze(str(venv)) == '''\
'''

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster==' + __version__)

    assert [
        req.split('==')[0]
        for req in pip_freeze(str(venv)).split()
    ] == ['pip-faster', 'virtualenv', 'wheel']

    run(str(venv.join('bin/pip-faster')), 'install', 'pure_python_package')

    assert 'pure-python-package==0.2.0' in pip_freeze(str(venv)).split('\n')


@pytest.mark.usefixtures('pypi_server')
def it_installs_stuff_from_requirements_file(tmpdir):
    tmpdir.chdir()

    venv = tmpdir.join('venv')
    run('virtualenv', str(venv))

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster==' + __version__)

    # An arbitrary small package: pure_python_package
    requirements('pure_python_package\nproject_with_c')

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')

    frozen_requirements = pip_freeze(str(venv)).split('\n')

    assert 'pure-python-package==0.2.0' in frozen_requirements
    assert 'project-with-c==0.1.0' in frozen_requirements


@pytest.mark.usefixtures('pypi_server')
def it_installs_stuff_with_dash_e_without_wheeling(tmpdir):
    from pip.wheel import Wheel

    tmpdir.chdir()

    venv = enable_coverage(tmpdir, 'venv')

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster==' + __version__)

    # Install a package from git with no extra dependencies in editable mode.
    #
    # We need to install a package from VCS instead of the filesystem because
    # otherwise we aren't testing that editable requirements aren't wheeled
    # (and instead might just be testing that local paths aren't wheeled).
    requirements('-e git+git://github.com/Yelp/dumb-init.git@87545be699a13d0fd31f67199b7782ebd446437e#egg=dumb-init')  # noqa

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')

    frozen_requirements = pip_freeze(str(venv)).split('\n')
    assert set(frozen_requirements) == set([
        '-e git://github.com/Yelp/dumb-init.git@87545be699a13d0fd31f67199b7782ebd446437e#egg=dumb_init-dev',  # noqa
        'coverage-enable-subprocess==0',
        'coverage==4.0.3',
        'pip-faster==' + __version__,
        'virtualenv==1.11.6',
        'wheel==0.29.0',
        '',
    ])

    # we shouldn't wheel things installed editable
    wheelhouse = tmpdir.join('home', '.cache', 'pip-faster', 'wheelhouse')
    assert set(Wheel(f.basename).name for f in wheelhouse.listdir()) == set([
        'coverage',
        'coverage-enable-subprocess',
    ])


@pytest.mark.usefixtures('pypi_server')
def it_doesnt_wheel_local_dirs(tmpdir):
    from pip.wheel import Wheel

    tmpdir.chdir()

    venv = enable_coverage(tmpdir, 'venv')

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster==' + __version__)

    run(
        venv.join('bin/pip-faster').strpath,
        'install',
        TOP.join('tests/testing/packages/dependant_package').strpath,
    )

    frozen_requirements = pip_freeze(str(venv)).split('\n')
    assert set(frozen_requirements) == set([
        'coverage==4.0.3',
        'coverage-enable-subprocess==0',
        'dependant-package==1',
        'implicit-dependency==1',
        'many-versions-package==3',
        'pip-faster==' + __version__,
        'pure-python-package==0.2.0',
        'virtualenv==1.11.6',
        'wheel==0.29.0',
        '',
    ])

    wheelhouse = tmpdir.join('home', '.cache', 'pip-faster', 'wheelhouse')
    assert set(Wheel(f.basename).name for f in wheelhouse.listdir()) == set([
        'coverage',
        'coverage-enable-subprocess',
        'implicit-dependency',
        'many-versions-package',
        'pure-python-package',
    ])


@pytest.mark.usefixtures('pypi_server')
def it_can_handle_requirements_already_met(tmpdir):
    tmpdir.chdir()

    venv = enable_coverage(tmpdir, 'venv')

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster==' + __version__)

    requirements('many-versions-package==1')

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')
    assert 'many-versions-package==1\n' in pip_freeze(str(venv))

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')
    assert 'many-versions-package==1\n' in pip_freeze(str(venv))
