from __future__ import absolute_import
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
    get_scenario('trivial')

    with io.open('requirements.txt', 'w') as reqs:
        reqs.write('doge==3.5.0')

    if sys.version_info[:2] == (2, 7):  # pragma: no cover PY27 only
        python_arg = '--python=python2.6'
    else:  # pragma: no cover PY26 only
        python_arg = '--python=python2.7'

    venv_update(python_arg)

    run('sh', '-c', '. virtualenv_run/bin/activate && doge --help')
