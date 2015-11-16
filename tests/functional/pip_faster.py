import pytest
from testing import run


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

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster')

    run('pip-faster', 'install', 'pure_python_package')
