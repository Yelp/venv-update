from __future__ import print_function
from __future__ import unicode_literals

from testing import run


def test_pip_install_flake8(tmpdir, capfd, sdist):
    tmpdir.chdir()

    run('virtualenv', 'myvenv')
    # surely there's a better way -.-
    run('myvenv/bin/pip', 'install', '--no-deps', sdist.strpath)
    run('myvenv/bin/pip', 'install', 'flake8')

    out, err = capfd.readouterr()  # flush buffers

    run('myvenv/bin/python', '-c', '''\
import json
from venv_update import pip_install
print(json.dumps(sorted(pip_install(('flake8',)))))
''')

    out, err = capfd.readouterr()
    assert err == ''

    from json import loads
    lastline = out.splitlines()[-1]
    assert loads(lastline) == ['flake8', 'mccabe', 'pep8', 'pyflakes']
