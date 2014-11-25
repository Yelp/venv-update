from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import io
import sys

from py._path.local import LocalPath as Path

from testing import get_scenario, run, venv_update

PY27 = sys.version_info[:2] == (2, 7)


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
        reqs.write('argparse\ndoge==3.5.0')

    python_arg = '--python=python' + ('2.7' if not PY27 else '2.6')

    venv_update(python_arg)

    run('sh', '-c', '. virtualenv_run/bin/activate && doge --help')
