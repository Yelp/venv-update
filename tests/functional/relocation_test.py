from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys

from testing import Path, requirements, run, venv_update

PY27 = sys.version_info[:2] == (2, 7)


def test_is_relocatable(tmpdir):
    tmpdir.chdir()
    requirements('')
    venv_update('--python=python')  # this makes pypy work right. derp.

    Path('virtualenv_run').rename('relocated')

    pip = 'relocated/bin/pip'
    assert Path(pip).exists()
    run(pip, '--version')


def test_is_relocatable_different_python_version(tmpdir):
    tmpdir.chdir()
    requirements('doge==3.5.0')

    python_arg = '--python=python' + ('2.6' if PY27 else '2.7')

    venv_update(python_arg)

    run('sh', '-c', '. virtualenv_run/bin/activate && doge --help')
