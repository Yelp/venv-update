from __future__ import print_function
from __future__ import unicode_literals

from testing import run


def set_up(tmpdir, sdist):
    tmpdir.chdir()

    run('virtualenv', 'myvenv')
    # surely there's a better way -.-
    # NOTE: `pip install TOP` causes an infinite copyfiles loop, under tox
    run('myvenv/bin/pip', 'install', '--no-deps', sdist.strpath)


def get_installed(capfd):
    out, err = capfd.readouterr()  # flush buffers

    run('myvenv/bin/python', '-c', '''\
import venv_update as v
for p in sorted(v.pip_get_installed()):
    print(p)''')

    out, err = capfd.readouterr()
    assert err == ''
    return out.split()


def test_pip_get_installed_empty(tmpdir, capfd, sdist):
    set_up(tmpdir, sdist)
    assert get_installed(capfd) == ['venv-update']


def test_pip_get_installed_flake8(tmpdir, capfd, sdist):
    set_up(tmpdir, sdist)
    run('myvenv/bin/pip', 'install', 'flake8')
    assert get_installed(capfd) == ['flake8', 'mccabe', 'pep8', 'pyflakes', 'venv-update']
