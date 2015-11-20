from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from testing import Path
from testing import requirements
from testing import run
from testing import venv_update
from testing import venv_update_symlink_pwd
from testing import pip_freeze
from testing import enable_coverage


@pytest.mark.usefixtures('pypi_server')
def test_python_versions(tmpdir):
    tmpdir.chdir()
    requirements('pure_python_package\ncoverage')
    enable_coverage(tmpdir)

    venv_update('--python=python2.6')
    run('sh', '-c', '. virtualenv_run/bin/activate && pure-python-script')
    out, err = run('sh', '-c', '. virtualenv_run/bin/activate && python --version')
    assert out == ''
    assert err.startswith('Python 2.6')

    venv_update('--python=python2.7')
    run('sh', '-c', '. virtualenv_run/bin/activate && pure-python-script')
    out, err = run('sh', '-c', '. virtualenv_run/bin/activate && python --version')
    assert out == ''
    assert err.startswith('Python 2.7')

    venv_update('--python=python2.6')
    run('sh', '-c', '. virtualenv_run/bin/activate && pure-python-script')
    out, err = run('sh', '-c', '. virtualenv_run/bin/activate && python --version')
    assert out == ''
    assert err.startswith('Python 2.6')


@pytest.mark.usefixtures('pypi_server')
def test_virtualenv_moved(tmpdir):
    """if you move the virtualenv and venv-update again, the old will be blown away, and things will work"""
    original_path = 'original'
    new_path = 'new_dir'

    with tmpdir.mkdir(original_path).as_cwd():
        requirements('pure_python_package')
        venv_update()
        run('virtualenv_run/bin/pure-python-script')
        run('virtualenv_run/bin/python', 'virtualenv_run/bin/pure-python-script')

    with tmpdir.as_cwd():
        Path(original_path).rename(new_path)

    with tmpdir.join(new_path).as_cwd():
        with pytest.raises(OSError) as excinfo:
            run('virtualenv_run/bin/pure-python-script')
        assert excinfo.type is OSError
        assert excinfo.value.args[0] == 2  # no such file
        run('virtualenv_run/bin/python', 'virtualenv_run/bin/pure-python-script')

        venv_update()
        run('virtualenv_run/bin/pure-python-script')
        run('virtualenv_run/bin/python', 'virtualenv_run/bin/pure-python-script')


@pytest.mark.usefixtures('pypi_server')
def test_recreate_active_virtualenv(tmpdir):
    with tmpdir.as_cwd():
        tmpenv = 'tmpenv'

        run('virtualenv', tmpenv)
        requirements('pure_python_package', 'reqs.txt')
        venv_update_symlink_pwd()
        run('tmpenv/bin/python', 'venv_update.py', tmpenv, 'reqs.txt')

        run('sh', '-c', '. tmpenv/bin/activate && pure-python-script')


@pytest.mark.usefixtures('pypi_server')
def test_update_while_active(tmpdir):
    tmpdir.chdir()
    requirements('virtualenv<2')

    venv_update()
    assert 'pure-python-package' not in pip_freeze()

    # An arbitrary small package: pure_python_package
    requirements('pure_python_package')

    venv_update_symlink_pwd()
    out, err = run('sh', '-c', '. virtualenv_run/bin/activate && python venv_update.py')

    assert err == ''
    assert out.startswith('Keeping virtualenv from previous run.\n')
    assert 'pure-python-package' in pip_freeze()


@pytest.mark.usefixtures('pypi_server')
def test_update_invalidated_while_active(tmpdir):
    tmpdir.chdir()
    requirements('virtualenv<2')

    venv_update()
    assert 'pure-python-package' not in pip_freeze()

    # An arbitrary small package: pure_python_package
    requirements('pure-python-package')

    venv_update_symlink_pwd()
    out, err = run('sh', '-c', '. virtualenv_run/bin/activate && python venv_update.py --system-site-packages')

    assert err == ''
    assert out.startswith('Removing invalidated virtualenv.\n')
    assert 'pure-python-package' in pip_freeze()
