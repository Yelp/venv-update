from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from testing import Path, requirements, run, venv_update


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
