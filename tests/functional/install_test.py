from __future__ import print_function
from __future__ import unicode_literals

from testing import run, venv_update_script


def test_pip_install_flake8(tmpdir, capfd):
    tmpdir.chdir()

    run('virtualenv', 'myvenv')
    run('myvenv/bin/pip', 'install', 'pep8')

    out, err = capfd.readouterr()  # flush buffers

    venv_update_script('''\
import json
from venv_update import pip_install, reqnames
print(json.dumps(sorted(reqnames(pip_install(('flake8',))))))
''', venv='myvenv')

    out, err = capfd.readouterr()
    assert err == ''

    from json import loads
    lastline = out.splitlines()[-1]
    assert loads(lastline) == ['flake8', 'mccabe', 'pep8', 'pyflakes']
