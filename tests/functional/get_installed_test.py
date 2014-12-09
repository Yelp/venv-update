from __future__ import print_function
from __future__ import unicode_literals

from testing import run, venv_update_script


def get_installed(capfd):
    out, err = capfd.readouterr()  # flush buffers

    venv_update_script('''\
import venv_update as v
for p in sorted(v.reqnames(v.pip_get_installed())):
    print(p)''', venv='myvenv')

    out, err = capfd.readouterr()
    assert err == ''
    return out.split()


def test_pip_get_installed(tmpdir, capfd):
    tmpdir.chdir()

    run('virtualenv', 'myvenv')
    assert get_installed(capfd) == []
    run('myvenv/bin/pip', 'install', 'flake8')
    assert get_installed(capfd) == ['flake8', 'mccabe', 'pep8', 'pyflakes']
    run('myvenv/bin/pip', 'uninstall', '--yes', 'flake8')
    assert get_installed(capfd) == ['mccabe', 'pep8', 'pyflakes']
