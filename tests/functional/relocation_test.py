from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import io
import sys

from py._path.local import LocalPath as Path

from testing import get_scenario, run, venv_update


def test_is_relocatable(tmpdir):
    tmpdir.chdir()
    get_scenario('trivial')
    venv_update()

    Path('virtualenv_run').rename('relocated')

    pip = 'relocated/bin/pip'
    assert Path(pip).exists()
    run(pip, '--version')


def test_is_relocatable_different_python_version(tmpdir):
    tmpdir.chdir()
    with io.open('requirements.txt', 'w') as reqs:
        reqs.write('doge==3.5.0')

    if sys.version_info[:2] == (2, 7):  # pragma: no cover PY27 only
        python_arg = '--python=python2.6'
    else:  # pragma: no cover PY26 only
        python_arg = '--python=python2.7'

    venv_update(python_arg)

    run('sh', '-c', '. virtualenv_run/bin/activate && doge --help')


def _get_virtualenv_data(capfd):
    out, err = capfd.readouterr()  # flush buffers
    Path('assertions.py').write('''
import json
import sys, virtualenv
print(json.dumps((virtualenv.__file__, sys.prefix, sys.real_prefix)))
''')
    run('virtualenv_run/bin/python', 'assertions.py')

    out, err = capfd.readouterr()
    assert err == ''

    from json import loads
    lastline = out.splitlines()[-1]
    return loads(lastline)


def path_is_within(path, within):
    from os.path import relpath
    return not relpath(path, within).startswith('..')


def test_is_relocatable_system_site_packages(tmpdir, capfd):
    tmpdir.chdir()
    requirements = Path('requirements.txt')

    # first show that virtualenv is installed to the system python
    # then show that virtualenv is installed to the virtualenv python, when it's required
    for reqs, invenv in (
            ('', False),
            ('virtualenv\n', True),
    ):
        requirements.write(reqs)
        venv_update('--system-site-packages')
        virtualenv__file__, prefix, real_prefix = _get_virtualenv_data(capfd)
        assert path_is_within(virtualenv__file__, prefix) == invenv
        assert path_is_within(virtualenv__file__, real_prefix) == (not invenv)
