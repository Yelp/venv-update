from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from sys import version_info

import pytest
from py._path.local import LocalPath as Path
from testing import requirements
from testing import run
from testing import strip_coverage_warnings
from testing import TOP
from testing import uncolor
from testing import venv_update
from testing import pip_freeze
from testing import enable_coverage

PY33 = (version_info >= (3, 3))


@pytest.mark.usefixtures('pypi_server')
def test_trivial(tmpdir):
    tmpdir.chdir()
    requirements('')
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
    enable_coverage(tmpdir, 'venv')
    venv_update('venv', 'requirements2.txt')
    assert pip_freeze('venv') == '\n'.join((
        'pip-faster==0.1.4.4',
        'six==1.8.0',
        'virtualenv==1.11.6',
        'wheel==0.26.0',
        ''
    ))


@pytest.mark.usefixtures('pypi_server')
def test_arguments_version(tmpdir):
    """Show that we can pass arguments through to virtualenv"""
    tmpdir.chdir()

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        # should show virtualenv version, then crash
        venv_update('--version')

    assert excinfo.value.returncode == 1
    out, err = excinfo.value.result
    err = strip_coverage_warnings(err)
    lasterr = err.rsplit('\n', 2)[-2]
    assert lasterr.startswith('virtualenv executable not found: /'), err
    assert lasterr.endswith('/virtualenv_run/bin/python'), err

    lines = [uncolor(line) for line in out.split('\n')]
    assert len(lines) == 3, lines
    assert lines[0].endswith('/virtualenv virtualenv_run --version'), repr(lines[0])


@pytest.mark.usefixtures('pypi_server')
def test_arguments_system_packages(tmpdir):
    """Show that we can pass arguments through to virtualenv"""
    tmpdir.chdir()
    requirements('')

    venv_update('--system-site-packages', 'virtualenv_run', 'requirements.txt')

    out, err = run('virtualenv_run/bin/python', '-c', '''\
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
    requirements('')

    venv_update()
    assert 'pure-python-package' not in pip_freeze()

    # An arbitrary url requirement.
    requirements('file://' + str(TOP / 'tests/testing/packages/pure_python_package'))

    venv_update()
    assert 'pure-python-package' in pip_freeze()


@pytest.mark.usefixtures('pypi_server_with_fallback')
def test_scripts_left_behind(tmpdir):
    tmpdir.chdir()
    requirements('')

    venv_update()

    # an arbitrary small package with a script: pep8
    script_path = Path('virtualenv_run/bin/pep8')
    assert not script_path.exists()

    run('virtualenv_run/bin/pip', 'install', 'pep8')
    assert script_path.exists()

    venv_update()
    assert not script_path.exists()


def assert_timestamps(*reqs):
    firstreq = Path(reqs[0])
    lastreq = Path(reqs[-1])

    venv_update('--python=python', 'virtualenv_run', *reqs)

    assert firstreq.mtime() < Path('virtualenv_run').mtime()

    # garbage, to cause a failure
    lastreq.write('-w wat')

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        venv_update('virtualenv_run', *reqs)

    assert excinfo.value.returncode == 2
    assert firstreq.mtime() > Path('virtualenv_run').mtime()

    # blank requirements should succeed
    lastreq.write('')

    venv_update('virtualenv_run', *reqs)
    assert Path(reqs[0]).mtime() < Path('virtualenv_run').mtime()


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
        ('venv-update', '--version'),
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
    uncolored = uncolor(result)
    assert uncolored.startswith('> ')
    # FIXME: Sometimes this is 'python -m', sometimes 'python2.7 -m'. Weird.
    assert uncolored.endswith('''\
/virtualenv virtualenv_run --version
1.11.6
''')

    return result, uncolored


def test_colored_tty(tmpdir):
    tmpdir.chdir()

    from os import openpty
    read, write = openpty()

    from testing.capture_subprocess import pty_normalize_newlines
    pty_normalize_newlines(read)

    out, uncolored = pipe_output(read, write)

    assert out != uncolored


def test_uncolored_pipe(tmpdir):
    tmpdir.chdir()

    from os import pipe
    read, write = pipe()

    out, uncolored = pipe_output(read, write)

    assert out == uncolored


def test_args_backward(tmpdir):
    tmpdir.chdir()
    requirements('')

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        venv_update('requirements.txt', 'myvenv')

    # py26 doesn't have a consistent exit code:
    #   http://bugs.python.org/issue15033
    assert excinfo.value.returncode != 0
    _, err = excinfo.value.result
    lasterr = strip_coverage_warnings(err).rsplit('\n', 2)[-2]
    errname = 'NotADirectoryError' if PY33 else 'OSError'
    assert lasterr.startswith(errname + ': [Errno 20] Not a directory'), err

    assert Path('requirements.txt').isfile()
    assert Path('requirements.txt').read() == ''
    assert not Path('myvenv').exists()


@pytest.mark.usefixtures('pypi_server')
def test_wrong_wheel(tmpdir):
    tmpdir.chdir()

    requirements('')
    venv_update('venv1', 'requirements.txt', '-ppython2.7')
    # A different python
    # Before fixing, this would install argparse using the `py2-none-any`
    # wheel, even on py3
    ret2out, _ = venv_update('venv2', 'requirements.txt', '-ppython3.3')

    assert 'py2-none-any' not in ret2out


def flake8_older():
    requirements('''\
flake8==2.0
# last pyflakes release before 0.8 was 0.7.3
pyflakes<0.8

# simply to prevent these from drifting:
mccabe<=0.3
pep8<=1.5.7
''')
    venv_update()
    assert pip_freeze() == '\n'.join((
        'flake8==2.0',
        'mccabe==0.3',
        'pep8==1.5.7',
        'pip-faster==0.1.4.4',
        'pyflakes==0.7.3',
        'virtualenv==1.11.6',
        'wheel==0.26.0',
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
''')
    venv_update()
    assert pip_freeze() == '\n'.join((
        'flake8==2.2.5',
        'mccabe==0.3',
        'pep8==1.5.7',
        'pip-faster==0.1.4.4',
        'pyflakes==0.8.1',
        'virtualenv==1.11.6',
        'wheel==0.26.0',
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


def utime(path, time):
    """set both mtime and atime of a py.path object"""
    from os import utime
    utime(path.strpath, (time, time))


@pytest.mark.skipif(True, reason='TODO: cache cleaning')
@pytest.mark.usefixtures('pypi_server')
def test_remove_stale_cache_values(tmpdir):
    """Tests that we remove stale (older than a week) cached packages
    and wheels, while still keeping everything created within the past week.
    """
    import time

    tmpdir.chdir()
    home_path = Path()

    pip_path = home_path / '.pip'
    cache_path = pip_path / 'cache'
    wheelhouse_path = pip_path / 'wheelhouse'

    stale_cached_package = cache_path / 'stale_package'
    fresh_cached_package = cache_path / 'new_package'

    stale_cached_wheel = wheelhouse_path / 'stale_wheel'
    fresh_cached_wheel = wheelhouse_path / 'new_wheel'

    # Creates a cached package and wheel in their respective
    # .pip/cache/ and .pip/wheelhouse directories.
    stale_cached_package.ensure(dir=True)
    fresh_cached_package.ensure(dir=True)
    stale_cached_wheel.ensure()
    fresh_cached_wheel.ensure()

    # Create some rough times for testing. These represent, in
    # seconds since epoch, a time from today, this week, and last month
    seconds_in_day = 86400
    now = time.time()
    this_week = now - seconds_in_day * 3
    last_month = now - seconds_in_day * 40

    # Set access times of stale package/wheel to be older than a week.
    utime(stale_cached_package, 0)  # Jan 1, 1970
    utime(stale_cached_wheel, last_month)

    # Set access times of fresh package/wheel to be within the past week.
    utime(fresh_cached_package, now)
    utime(fresh_cached_wheel, this_week)

    requirements('')
    venv_update()

    # Assert that we can no longer access the stale package/wheel
    # that have been removed.
    assert not stale_cached_package.exists()
    assert not stale_cached_wheel.exists()

    # Assert that we can still access the fresh package/wheel,
    # they should not have been removed.
    assert fresh_cached_package.exists()
    assert fresh_cached_wheel.exists()
