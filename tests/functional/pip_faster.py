from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest
from pip.wheel import Wheel

from testing import install_coverage
from testing import pip_freeze
from testing import requirements
from testing import run
from testing import TOP
from testing import uncolor
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
    install_coverage(venv)

    assert pip_freeze(str(venv)) == '''\
coverage==4.0.3
coverage-enable-subprocess==1.0
'''

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'venv-update==' + __version__)

    assert [
        req.split('==')[0]
        for req in pip_freeze(str(venv)).split()
    ] == ['coverage', 'coverage-enable-subprocess', 'venv-update', 'wheel']

    run(str(venv.join('bin/pip-faster')), 'install', 'pure_python_package')

    assert 'pure-python-package==0.2.1' in pip_freeze(str(venv)).split('\n')


@pytest.mark.usefixtures('pypi_server')
def it_installs_stuff_from_requirements_file(tmpdir):
    venv = tmpdir.join('venv')
    install_coverage(venv)

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'venv-update==' + __version__)

    # An arbitrary small package: pure_python_package
    requirements('pure_python_package\nproject_with_c')

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')

    frozen_requirements = pip_freeze(str(venv)).split('\n')

    assert 'pure-python-package==0.2.1' in frozen_requirements
    assert 'project-with-c==0.1.0' in frozen_requirements


@pytest.mark.usefixtures('pypi_server')
def it_installs_stuff_with_dash_e_without_wheeling(tmpdir):
    venv = tmpdir.join('venv')
    install_coverage(venv)

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'venv-update==' + __version__)

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
        'coverage-enable-subprocess==1.0',
        'coverage==4.0.3',
        'venv-update==' + __version__,
        'wheel==0.29.0',
        '',
    ])

    # we shouldn't wheel things installed editable
    wheelhouse = tmpdir.join('home', '.cache', 'pip-faster', 'wheelhouse')
    assert set(Wheel(f.basename).name for f in wheelhouse.listdir()) == set([
    ])


@pytest.mark.usefixtures('pypi_server')
def it_doesnt_wheel_local_dirs(tmpdir):
    venv = tmpdir.join('venv')
    install_coverage(venv)

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'venv-update==' + __version__)

    run(
        venv.join('bin/pip-faster').strpath,
        'install',
        TOP.join('tests/testing/packages/dependant_package').strpath,
    )

    frozen_requirements = pip_freeze(str(venv)).split('\n')
    assert set(frozen_requirements) == set([
        'coverage==4.0.3',
        'coverage-enable-subprocess==1.0',
        'dependant-package==1',
        'implicit-dependency==1',
        'many-versions-package==3',
        'pure-python-package==0.2.1',
        'venv-update==' + __version__,
        'wheel==0.29.0',
        '',
    ])

    wheelhouse = tmpdir.join('home', '.cache', 'pip-faster', 'wheelhouse')
    assert set(Wheel(f.basename).name for f in wheelhouse.listdir()) == set([
        'implicit-dependency',
        'many-versions-package',
        'pure-python-package',
    ])


@pytest.mark.usefixtures('pypi_server')
def it_doesnt_wheel_git_repos(tmpdir):
    venv = tmpdir.join('venv')
    install_coverage(venv)

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'venv-update==' + __version__)

    run(
        venv.join('bin/pip-faster').strpath,
        'install',
        'git+git://github.com/Yelp/dumb-init.git@87545be699a13d0fd31f67199b7782ebd446437e#egg=dumb-init',  # noqa
    )

    frozen_requirements = pip_freeze(str(venv)).split('\n')
    assert set(frozen_requirements) == set([
        'coverage-enable-subprocess==1.0',
        'coverage==4.2',
        'dumb-init==0.5.0',
        'venv-update==' + __version__,
        'wheel==0.29.0',
        '',
    ])

    wheelhouse = tmpdir.join('home', '.cache', 'pip-faster', 'wheelhouse')
    assert set(Wheel(f.basename).name for f in wheelhouse.listdir()) == set()


@pytest.mark.usefixtures('pypi_server')
def it_can_handle_requirements_already_met(tmpdir):
    venv = tmpdir.join('venv')
    install_coverage(venv)

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'venv-update==' + __version__)

    requirements('many-versions-package==1')

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')
    assert 'many-versions-package==1\n' in pip_freeze(str(venv))

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')
    assert 'many-versions-package==1\n' in pip_freeze(str(venv))


@pytest.mark.usefixtures('pypi_server')
def it_gives_proper_error_without_requirements(tmpdir):
    venv = tmpdir.join('venv')
    install_coverage(venv)

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'venv-update==' + __version__)

    out, err = run(str(venv.join('bin/pip-faster')), 'install')
    out = uncolor(out)
    assert out.startswith('You must give at least one requirement to install')
    assert err == ''


@pytest.mark.usefixtures('pypi_server')
def it_can_handle_a_bad_findlink(tmpdir):
    venv = tmpdir.join('venv')
    install_coverage(venv)

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'venv-update==' + __version__)

    out, err = run(
        str(venv.join('bin/pip-faster')),
        'install', '-vvv',
        '--find-links', 'git+wat://not/a/thing',
        'pure-python-package',
    )
    out = uncolor(out)

    assert '''
Candidate wheel: pure_python_package-0.2.1-py2.py3-none-any.whl
Installing collected packages: pure-python-package
Successfully installed pure-python-package
''' in out
    assert err == ''
    assert 'pure-python-package==0.2.1' in pip_freeze(str(venv)).split('\n')
