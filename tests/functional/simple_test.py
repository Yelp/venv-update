from __future__ import print_function
from __future__ import unicode_literals
from py._path.local import LocalPath as Path
import pytest

from testing import get_scenario, run, strip_coverage_warnings, venv_update

from sys import version_info
PY33 = (version_info >= (3, 3))


def test_trivial(tmpdir):
    tmpdir.chdir()
    get_scenario('trivial')
    venv_update()


@pytest.mark.flaky(reruns=10)
def test_second_install_faster(tmpdir):
    """install twice, and the second one should be faster, due to whl caching"""
    tmpdir.chdir()
    get_scenario('trivial')

    with open('requirements.txt', 'w') as requirements:
        # An arbitrary package that takes a bit of time to install: twisted
        # Should I make my own fake c-extention just to remove this dependency?
        requirements.write('''\
simplejson
pyyaml
coverage
pylint
pytest
pep8==1.0
''')

    from time import time
    start = time()
    venv_update()
    time1 = time() - start

    start = time()
    venv_update()
    time2 = time() - start

    # second install should be at least twice as fast
    ratio = time1 / time2
    print('%.2fx speedup' % ratio)
    assert ratio > 4


def test_arguments_version(tmpdir, capfd):
    """Show that we can pass arguments through to virtualenv"""
    tmpdir.chdir()

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        # should show virtualenv version, then crash
        venv_update('--version')

    assert excinfo.value.returncode == 1
    out, err = capfd.readouterr()
    lasterr = strip_coverage_warnings(err).rsplit('\n', 2)[-2]
    if PY33:
        errname = 'FileNotFoundError'
    else:
        errname = 'OSError'
    assert lasterr.startswith(errname + ': [Errno 2] No such file or directory'), err

    lines = out.split('\n')
    assert lines[-4] == ('> virtualenv virtualenv_run --version'), out
    assert lines[-2].startswith('> /'), out
    assert lines[-2].endswith('venv_update.py --stage2 virtualenv_run requirements.txt --version'), out


def test_arguments_system_packages(tmpdir, capfd):
    """Show that we can pass arguments through to virtualenv"""
    tmpdir.chdir()
    get_scenario('trivial')

    venv_update('--system-site-packages', 'virtualenv_run', 'requirements.txt')
    out, err = capfd.readouterr()  # flush buffers

    run('virtualenv_run/bin/python', '-c', '''\
import sys
for p in sys.path:
    if p.startswith(sys.real_prefix) and p.endswith("-packages"):
        print(p)
        break
''')
    out, err = capfd.readouterr()
    assert strip_coverage_warnings(err) == ''
    out = out.rstrip('\n')
    assert out and Path(out).isdir()


def pip(*args):
    # because the scripts are made relative, it won't use the venv python without being explicit.
    run('virtualenv_run/bin/python', 'virtualenv_run/bin/pip', *args)


def pip_freeze(capfd):
    out, err = capfd.readouterr()  # flush any previous output

    pip('freeze')
    out, err = capfd.readouterr()

    assert strip_coverage_warnings(err) == ''
    return out


def test_update_while_active(tmpdir, capfd):
    tmpdir.chdir()
    get_scenario('trivial')

    venv_update()
    assert 'mccabe' not in pip_freeze(capfd)

    with open('requirements.txt', 'w') as requirements:
        # An arbitrary small package: mccabe
        requirements.write('mccabe')

    run('sh', '-c', '. virtualenv_run/bin/activate && venv-update')
    assert 'mccabe' in pip_freeze(capfd)


def test_scripts_left_behind(tmpdir):
    tmpdir.chdir()
    get_scenario('trivial')

    venv_update()

    # an arbitrary small package with a script: pep8
    script_path = Path('virtualenv_run/bin/pep8')
    assert not script_path.exists()

    pip('install', 'pep8')
    assert script_path.exists()

    venv_update()
    assert not script_path.exists()


def assert_timestamps(*reqs):
    get_scenario('trivial')
    venv_update('virtualenv_run', *reqs)

    assert Path(reqs[0]).mtime() < Path('virtualenv_run').mtime()

    with open(reqs[-1], 'w') as requirements:
        # garbage, to cause a failure
        requirements.write('-w wat')

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        venv_update('virtualenv_run', *reqs)

    assert excinfo.value.returncode == 1
    assert Path(reqs[0]).mtime() > Path('virtualenv_run').mtime()

    with open(reqs[-1], 'w') as requirements:
        # blank requirements should succeed
        requirements.write('')

    venv_update('virtualenv_run', *reqs)
    assert Path(reqs[0]).mtime() < Path('virtualenv_run').mtime()


def test_timestamps_single(tmpdir):
    tmpdir.chdir()
    assert_timestamps('requirements.txt')


def test_timestamps_multiple(tmpdir):
    tmpdir.chdir()
    with open('requirements2.txt', 'w') as requirements:
        requirements.write('')
    assert_timestamps('requirements.txt', 'requirements2.txt')


def readall(fd):
    """My own read loop, bc the one in python3.4 is derpy atm:
    http://bugs.python.org/issue21090#msg231093
    """
    from os import read
    result = []
    lastread = None
    while lastread != b'':
        try:
            lastread = read(fd, 4 * 1024)
        except OSError as error:
            if error.errno == 5:  # pty end-of-file  -.-
                break
            else:
                raise
        result.append(lastread)
    return b''.join(result).decode('US-ASCII')


def pipe_output(read, write):
    from os import environ
    environ = environ.copy()
    environ['HOME'] = str(Path('.').realpath())

    from subprocess import Popen
    vupdate = Popen(
        ('venv-update', '--version'),
        env=environ,
        stdout=write,
        close_fds=True,
    )

    from os import close
    close(write)
    result = readall(read)
    close(read)
    vupdate.wait()
    return result


def unprintable(mystring):
    """return only the unprintable characters of a string"""
    from string import printable
    return ''.join(
        character
        for character in mystring
        if character not in printable
    )


def test_colored_tty():
    from os import openpty
    read, write = openpty()

    out = pipe_output(read, write)

    assert unprintable(out), out


def test_uncolored_pipe():
    from os import pipe
    read, write = pipe()

    out = pipe_output(read, write)

    assert not unprintable(out), out
