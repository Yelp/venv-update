from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from sys import version_info

import pytest
from py._path.local import LocalPath as Path

from testing import enable_coverage
from testing import install_coverage
from testing import OtherPython
from testing import pip_freeze
from testing import requirements
from testing import run
from testing import strip_coverage_warnings
from testing import strip_pip_warnings
from testing import TOP
from testing import uncolor
from testing import venv_update
from venv_update import __version__

PY33 = (version_info >= (3, 3))


@pytest.mark.usefixtures('pypi_server')
def test_trivial(tmpdir):
    tmpdir.chdir()
    requirements('')
    enable_coverage()
    venv_update()


@pytest.mark.usefixtures('pypi_server_with_fallback')
def test_install_custom_path_and_requirements(tmpdir):
    """Show that we can install to a custom directory with a custom
    requirements file."""
    tmpdir.chdir()
    requirements(
        'six==1.8.0\n',
        path='requirements2.txt',
    )
    enable_coverage()
    venv_update('venv=', 'venv2', 'install=', '-r', 'requirements2.txt')
    assert pip_freeze('venv2') == '\n'.join((
        'six==1.8.0',
        'venv-update==' + __version__,
        'wheel==0.29.0',
        ''
    ))


@pytest.mark.usefixtures('pypi_server')
def test_arguments_version(tmpdir):
    """Show that we can pass arguments through to virtualenv"""
    tmpdir.chdir()
    enable_coverage()

    # should show virtualenv version, successfully
    out, err = venv_update('venv=', '--version')
    err = strip_pip_warnings(err)
    assert err == ''

    out = uncolor(out)
    lines = out.splitlines()
    # 13:py27 14:py35 15:pypy
    assert len(lines) == 8, repr(lines)
    assert lines[-2] == '> virtualenv --version', repr(lines)


@pytest.mark.usefixtures('pypi_server')
def test_arguments_system_packages(tmpdir):
    """Show that we can pass arguments through to virtualenv"""
    tmpdir.chdir()
    requirements('')

    venv_update('venv=', '--system-site-packages', 'venv')

    out, err = run('venv/bin/python', '-c', '''\
import sys
for p in sys.path:
    if p.startswith(sys.real_prefix) and p.endswith("-packages"):
        print(p)
        break
''')
    assert err == ''
    out = out.rstrip('\n')
    assert out and Path(out).isdir()


@pytest.mark.usefixtures('pypi_server')
def test_eggless_url(tmpdir):
    tmpdir.chdir()

    enable_coverage()

    # An arbitrary url requirement.
    requirements('-e file://' + str(TOP / 'tests/testing/packages/pure_python_package'))

    venv_update()
    assert 'pure-python-package' in pip_freeze()


@pytest.mark.usefixtures('pypi_server_with_fallback')
def test_scripts_left_behind(tmpdir):
    tmpdir.chdir()
    requirements('')

    venv_update()

    # an arbitrary small package with a script: pep8
    script_path = Path('venv/bin/pep8')
    assert not script_path.exists()

    run('venv/bin/pip', 'install', 'pep8')
    assert script_path.exists()

    venv_update()
    assert not script_path.exists()


def assert_timestamps(*reqs):
    firstreq = Path(reqs[0])
    lastreq = Path(reqs[-1])
    args = ['install='] + sum([['-r', req] for req in reqs], [])

    venv_update(*args)

    assert firstreq.mtime() < Path('venv').mtime()

    # garbage, to cause a failure
    lastreq.write('-w wat')

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        venv_update(*args)

    assert excinfo.value.returncode == 2
    assert firstreq.mtime() > Path('venv').mtime()

    # blank requirements should succeed
    lastreq.write('')

    venv_update(*args)
    assert firstreq.mtime() < Path('venv').mtime()


@pytest.mark.usefixtures('pypi_server')
def test_timestamps_single(tmpdir):
    tmpdir.chdir()
    requirements('')
    assert_timestamps('requirements.txt')


@pytest.mark.usefixtures('pypi_server')
def test_timestamps_multiple(tmpdir):
    tmpdir.chdir()
    requirements('')
    Path('requirements2.txt').write('')
    assert_timestamps('requirements.txt', 'requirements2.txt')


def pipe_output(read, write):
    from os import environ
    environ = environ.copy()

    from subprocess import Popen
    vupdate = Popen(
        ('venv-update', 'venv=', '--version'),
        env=environ,
        stdout=write,
        close_fds=True,
    )

    from os import close
    from testing.capture_subprocess import read_all
    close(write)
    result = read_all(read)
    vupdate.wait()

    result = result.decode('US-ASCII')
    print(result)
    uncolored = uncolor(result)
    assert uncolored.startswith('> ')
    # FIXME: Sometimes this is 'python -m', sometimes 'python2.7 -m'. Weird.
    import virtualenv
    assert uncolored.endswith('''
> virtualenv --version
%s
''' % virtualenv.__version__)

    return result, uncolored


@pytest.mark.usefixtures('pypi_server')
def test_colored_tty(tmpdir):
    tmpdir.chdir()

    from os import openpty
    read, write = openpty()

    from testing.capture_subprocess import pty_normalize_newlines
    pty_normalize_newlines(read)

    out, uncolored = pipe_output(read, write)

    assert out != uncolored


@pytest.mark.usefixtures('pypi_server')
def test_uncolored_pipe(tmpdir):
    tmpdir.chdir()

    from os import pipe
    read, write = pipe()

    out, uncolored = pipe_output(read, write)

    assert out == uncolored


@pytest.mark.usefixtures('pypi_server')
def test_args_backward(tmpdir):
    tmpdir.chdir()
    enable_coverage()
    requirements('')

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        venv_update('venv=', 'requirements.txt')

    # py26 doesn't have a consistent exit code:
    #   http://bugs.python.org/issue15033
    assert excinfo.value.returncode != 0
    out, err = excinfo.value.result
    err = strip_coverage_warnings(err)
    err = strip_pip_warnings(err)
    assert err == ''
    out = uncolor(out)
    assert out.rsplit('\n', 4)[-4:] == [
        '> virtualenv requirements.txt',
        'ERROR: File already exists and is not a directory.',
        'Please provide a different path or delete the file.',
        '',
    ]

    assert Path('requirements.txt').isfile()
    assert Path('requirements.txt').read() == ''
    assert not Path('myvenv').exists()


@pytest.mark.usefixtures('pypi_server')
def test_wrong_wheel(tmpdir):
    tmpdir.chdir()

    requirements('pure_python_package==0.1.0')
    venv_update('venv=', 'venv1')
    # A different python
    # Before fixing, this would install argparse using the `py2-none-any`
    # wheel, even on py3
    other_python = OtherPython()
    ret2out, _ = venv_update('venv=', 'venv2', '-p' + other_python.interpreter, 'install=', '-vv', '-r', 'requirements.txt')

    assert '''
  No wheel found locally for pinned requirement pure-python-package==0.1.0 (from -r requirements.txt (line 1))
''' in uncolor(ret2out)


def flake8_older():
    requirements('''\
flake8==2.0
# last pyflakes release before 0.8 was 0.7.3
pyflakes<0.8

# simply to prevent these from drifting:
mccabe<=0.3
pep8<=1.5.7

-r %s/requirements.d/coverage.txt
''' % TOP)
    venv_update()
    assert pip_freeze() == '\n'.join((
        'coverage==X.Y',
        'coverage-enable-subprocess==1.0',
        'flake8==2.0',
        'mccabe==0.3',
        'pep8==1.5.7',
        'pyflakes==0.7.3',
        'venv-update==' + __version__,
        'wheel==0.29.0',
        ''
    ))


def flake8_newer():
    requirements('''\
flake8==2.2.5
# we expect 0.8.1
pyflakes<=0.8.1

# simply to prevent these from drifting:
mccabe<=0.3
pep8<=1.5.7

-r %s/requirements.d/coverage.txt
''' % TOP)
    venv_update()
    assert pip_freeze() == '\n'.join((
        'coverage==X.Y',
        'coverage-enable-subprocess==1.0',
        'flake8==2.2.5',
        'mccabe==0.3',
        'pep8==1.5.7',
        'pyflakes==0.8.1',
        'venv-update==' + __version__,
        'wheel==0.29.0',
        ''
    ))


@pytest.mark.usefixtures('pypi_server_with_fallback')
def test_upgrade(tmpdir):
    tmpdir.chdir()
    flake8_older()
    flake8_newer()


@pytest.mark.usefixtures('pypi_server_with_fallback')
def test_downgrade(tmpdir):
    tmpdir.chdir()
    flake8_newer()
    flake8_older()


@pytest.mark.usefixtures('pypi_server')
def test_package_name_normalization(tmpdir):
    with tmpdir.as_cwd():
        enable_coverage()
        requirements('WEIRD_cAsing-packAge')

        venv_update()
        assert '\nweird-CASING-pACKage==' in pip_freeze()


@pytest.mark.usefixtures('pypi_server')
def test_override_requirements_file(tmpdir):
    tmpdir.chdir()
    enable_coverage()
    requirements('')
    Path('.').join('requirements-bootstrap.txt').write('''\
venv-update==%s
pure_python_package
''' % __version__)
    out, err = venv_update(
        'bootstrap-deps=', '-r', 'requirements-bootstrap.txt',
    )
    err = strip_pip_warnings(err)
    assert err == ''

    out = uncolor(out)
    assert (
        '\n> pip install --find-links=file://%s/home/.cache/pip-faster/wheelhouse -r requirements-bootstrap.txt\n' % tmpdir
    ) in out
    assert (
        '\nSuccessfully installed pip-1.5.6 pure-python-package-0.2.1 venv-update-%s' % __version__
    ) in out
    assert '\n  Successfully uninstalled pure-python-package\n' in out

    expected = '\n'.join((
        'venv-update==%s' % __version__,
        'wheel==0.29.0',
        ''
    ))
    assert pip_freeze() == expected


@pytest.mark.usefixtures('pypi_server')
def test_cant_wheel_package(tmpdir):
    with tmpdir.as_cwd():
        enable_coverage()
        install_coverage()
        requirements('cant-wheel-package\npure-python-package')

        out, err = venv_update()
        err = strip_pip_warnings(err)
        assert err == ''

        out = uncolor(out)

        # for unknown reasons, py27 has an extra line with four spaces in this output, where py26 does not.
        out = out.replace('\n    \n', '\n')
        assert '''

----------------------------------------
Failed building wheel for cant-wheel-package
Running setup.py bdist_wheel for pure-python-package
Destination directory: %s/home/.cache/pip-faster/wheelhouse''' % tmpdir + '''
SLOW!! no wheel found after building (couldn't be wheeled?): cant-wheel-package==0.1.0
Installing collected packages: cant-wheel-package, pure-python-package
  Running setup.py install for cant-wheel-package
  Could not find .egg-info directory in install record for cant-wheel-package (from -r requirements.txt (line 1))
Successfully installed cant-wheel-package pure-python-package
Cleaning up...
''' in out  # noqa
        assert pip_freeze().startswith('cant-wheel-package==0.1.0\n')


@pytest.mark.usefixtures('pypi_server')
def test_has_extras(tmpdir):
    with tmpdir.as_cwd():
        enable_coverage()
        install_coverage()
        requirements('pure-python-package[my-extra]')

        for _ in range(2):
            venv_update()

            expected = '\n'.join((
                'implicit-dependency==1',
                'pure-python-package==0.2.1',
                'venv-update==%s' % __version__,
                'wheel==0.29.0',
                ''
            ))
            assert pip_freeze() == expected
