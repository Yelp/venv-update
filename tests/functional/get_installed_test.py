from __future__ import print_function
from __future__ import unicode_literals

from testing import run, Path
import venv_update


def set_up(tmpdir):
    tmpdir.chdir()

    run('virtualenv', 'myvenv')
    # surely there's a better way -.-
    # NOTE: `pip install TOP` causes an infinite copyfiles loop, under tox
    Path(venv_update.__file__).copy(tmpdir)


def get_installed(capfd):
    out, err = capfd.readouterr()  # flush buffers

    run('myvenv/bin/python', '-c', '''\
import venv_update as v
for p in sorted(v.pip_get_installed()):
    print(p)''')

    out, err = capfd.readouterr()
    assert err == ''
    return out.split()


def test_pip_get_installed(tmpdir, capfd):
    set_up(tmpdir)
    assert get_installed(capfd) == []
    run('myvenv/bin/pip', 'install', 'flake8')
    assert get_installed(capfd) == ['flake8', 'mccabe', 'pep8', 'pyflakes']
    run('myvenv/bin/pip', 'uninstall', '--yes', 'flake8')
    assert get_installed(capfd) == ['mccabe', 'pep8', 'pyflakes']
