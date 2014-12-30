from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from testing import Path, requirements, run, venv_update


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
