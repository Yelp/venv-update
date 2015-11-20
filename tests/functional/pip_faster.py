import pytest
from testing import requirements
from testing import run

from functional.simple_test import pip_freeze


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


@pytest.mark.usefixtures('pypi_server_with_fallback')
def it_installs_stuff_from_requirements_file(tmpdir):
    tmpdir.chdir()

    venv = tmpdir.join('venv')
    run('virtualenv', str(venv))

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster')

    # An arbitrary small package: mccabe
    requirements('mccabe\npep8==1.0')

    run(str(venv.join('bin/pip-faster')), 'install', '-r', 'requirements.txt')
