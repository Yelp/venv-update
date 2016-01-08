from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from testing import enable_coverage
from testing import OtherPython
from testing import Path
from testing import pip_freeze
from testing import requirements
from testing import run
from testing import TOP
from testing import venv_update
from testing import venv_update_symlink_pwd


def assert_c_extension_runs():
    out, err = run('venv/bin/c-extension-script')
    assert err == ''
    assert out == 'hello world\n'

    out, err = run('sh', '-c', '. venv/bin/activate && c-extension-script')
    assert err == ''
    assert out == 'hello world\n'


def assert_python_version(version):
    outputs = run('sh', '-c', '. venv/bin/activate && python -c "import sys; print(sys.version)"')

    # older versions of python output on stderr, newer on stdout, but we dont care too much which
    assert '' in outputs
    actual_version = ''.join(outputs)
    assert actual_version.startswith(version)
    return actual_version


@pytest.mark.usefixtures('pypi_server')
def test_python_versions(tmpdir):
    tmpdir.chdir()
    requirements('project-with-c')

    def run_with_coverage(*options):
        enable_coverage(tmpdir, options=options)
        venv_update(*options)

    other_python = OtherPython()
    run_with_coverage('--python=' + other_python.interpreter)
    assert_c_extension_runs()
    assert_python_version(other_python.version_prefix)

    from sys import executable as python
    run_with_coverage('--python=' + python)
    assert_c_extension_runs()
    from sys import version
    assert_python_version(version)

    run_with_coverage('--python=' + other_python.interpreter)
    assert_c_extension_runs()
    assert_python_version(other_python.version_prefix)


@pytest.mark.usefixtures('pypi_server')
def test_virtualenv_moved(tmpdir):
    """if you move the virtualenv and venv-update again, the old will be blown away, and things will work"""
    original_path = 'original'
    new_path = 'new_dir'

    with tmpdir.mkdir(original_path).as_cwd():
        requirements('project_with_c')
        venv_update()
        assert_c_extension_runs()

    with tmpdir.as_cwd():
        Path(original_path).rename(new_path)

    with tmpdir.join(new_path).as_cwd():
        with pytest.raises(OSError) as excinfo:
            assert_c_extension_runs()
        # python >= 3.3 raises FileNotFoundError
        assert excinfo.type.__name__ in ('OSError', 'FileNotFoundError')
        assert excinfo.value.args[0] == 2  # no such file

        venv_update()
        assert_c_extension_runs()


@pytest.mark.usefixtures('pypi_server')
def test_recreate_active_virtualenv(tmpdir):
    with tmpdir.as_cwd():
        run('virtualenv', 'venv')
        run('venv/bin/pip', 'install', '-r', str(TOP / 'requirements.d/coverage.txt'))

        requirements('project_with_c')
        venv_update_symlink_pwd()
        run('venv/bin/python', 'venv_update.py')

        assert_c_extension_runs()


@pytest.mark.usefixtures('pypi_server')
def test_update_while_active(tmpdir):
    tmpdir.chdir()
    requirements('virtualenv<2')

    venv_update()
    assert 'project-with-c' not in pip_freeze()

    # An arbitrary small package: project_with_c
    requirements('project_with_c')

    venv_update_symlink_pwd()
    out, err = run('sh', '-c', '. venv/bin/activate && python venv_update.py')

    assert err == ''
    assert out.startswith('Keeping virtualenv from previous run.\n')
    assert 'project-with-c' in pip_freeze()


@pytest.mark.usefixtures('pypi_server')
def test_update_invalidated_while_active(tmpdir):
    tmpdir.chdir()
    requirements('virtualenv<2')

    venv_update()
    assert 'project-with-c' not in pip_freeze()

    # An arbitrary small package: project_with_c
    requirements('project-with-c')

    venv_update_symlink_pwd()
    out, err = run('sh', '-c', '. venv/bin/activate && python venv_update.py --system-site-packages')

    assert err == ''
    assert out.startswith('Removing invalidated virtualenv.\n')
    assert 'project-with-c' in pip_freeze()
