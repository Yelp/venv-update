from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from testing import Path
from testing import requirements
from testing import run
from testing import venv_update


@pytest.mark.usefixtures('pypi_server')
def test_relocatable(tmpdir):
    tmpdir.chdir()
    requirements('')
    venv_update('--python=python')  # this makes pypy work right. derp.

    Path('virtualenv_run').rename('relocated')

    python = 'relocated/bin/python'
    assert Path(python).exists()
    run(python, '-m', 'pip.__main__', '--version')


def test_python_versions(tmpdir):
    tmpdir.chdir()
    requirements('doge==3.5.0')

    venv_update('--python=python2.6')
    run('sh', '-c', '. virtualenv_run/bin/activate && doge --help')
    out, err = run('sh', '-c', '. virtualenv_run/bin/activate && python --version')
    assert out == ''
    assert err.startswith('Python 2.6')

    venv_update('--python=python2.7')
    run('sh', '-c', '. virtualenv_run/bin/activate && doge --help')
    out, err = run('sh', '-c', '. virtualenv_run/bin/activate && python --version')
    assert out == ''
    assert err.startswith('Python 2.7')

    venv_update('--python=python2.6')
    run('sh', '-c', '. virtualenv_run/bin/activate && doge --help')
    out, err = run('sh', '-c', '. virtualenv_run/bin/activate && python --version')
    assert out == ''
    assert err.startswith('Python 2.6')


def test_virtualenv_moved(tmpdir):
    """if you move the virtualenv and venv-update again, the old will be blown away, and things will work"""
    original_path = 'original'
    new_path = 'new_dir'

    tmpdir.mkdir(original_path).chdir()
    requirements('flake8==2.4.0\n')
    Path('run.py').write('')
    venv_update()
    run('virtualenv_run/bin/flake8', 'run.py')
    run('virtualenv_run/bin/python', 'virtualenv_run/bin/flake8', 'run.py')

    tmpdir.chdir()
    Path(original_path).rename(new_path)
    tmpdir.join(new_path).chdir()
    venv_update()
    run('virtualenv_run/bin/flake8', 'run.py')
    run('virtualenv_run/bin/python', 'virtualenv_run/bin/flake8', 'run.py')
