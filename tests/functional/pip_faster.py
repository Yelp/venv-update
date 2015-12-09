from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest
from functional.simple_test import pip_freeze
from testing import requirements
from testing import run
from testing import TOP


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
    run(pip, 'install', 'pip-faster')

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
    run(pip, 'install', 'pip-faster')

    # An arbitrary small package: pure_python_package
    requirements('pure_python_package\nproject_with_c')

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')

    frozen_requirements = pip_freeze(str(venv)).split('\n')

    assert 'pure-python-package==0.2.0' in frozen_requirements
    assert 'project-with-c==0.1.0' in frozen_requirements


@pytest.mark.usefixtures('pypi_server')
def it_installs_stuff_with_dash_e(tmpdir):
    tmpdir.chdir()

    venv = tmpdir.join('venv')
    run('virtualenv', str(venv))

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster')

    requirements('-e ' + TOP.join('tests/testing/packages/dependant_package').strpath)

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')

    frozen_requirements = pip_freeze(str(venv)).split('\n')

    assert 'dependant-package==1' in frozen_requirements
    assert 'implicit-dependency==1' in frozen_requirements
    assert 'pure-python-package==0.2.0' in frozen_requirements
