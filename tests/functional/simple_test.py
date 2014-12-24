from __future__ import print_function
from __future__ import unicode_literals
from py._path.local import LocalPath as Path
import pytest

from testing import (
    TOP,
    requirements,
    run,
    strip_coverage_warnings,
    uncolor,
    venv_update,
    venv_update_symlink_pwd,
)

from sys import version_info
PY33 = (version_info >= (3, 3))


def test_trivial(tmpdir):
    tmpdir.chdir()
    requirements('')
    venv_update()


def enable_coverage(tmpdir):
    venv = tmpdir.join('virtualenv_run')
    if not venv.isdir():
        run('virtualenv', venv.strpath)
    run(
        venv.join('bin/python').strpath,
        '-m', 'pip.__main__',
        'install',
        '-r', TOP.join('requirements.d/coverage.txt').strpath,
    )


def install_twice(tmpdir, between):
    """install twice, and the second one should be faster, due to whl caching"""
    tmpdir.chdir()

    # Arbitrary packages that takes a bit of time to install:
    # Should I make a fixture c-extention to remove these dependencies?
    # NOTE: Avoid projects that use 2to3 (urwid). It makes the runtime vary too widely.
    requirements('''\
simplejson==3.6.5
pyyaml==3.11
pylint==1.4.0
pytest==2.6.4
unittest2==0.8.0
chroniker
''')

    from time import time
    enable_coverage(tmpdir)
    assert pip_freeze() == '\n'.join((
        'cov-core==1.15.0',
        'coverage==4.0a1',
        ''
    ))

    start = time()
    venv_update()
    time1 = time() - start
    assert pip_freeze() == '\n'.join((
        'PyYAML==3.11',
        'argparse==1.2.1',
        'astroid==1.3.2',
        'chroniker==0.0.0',
        'logilab-common==0.63.2',
        'py==1.4.26',
        'pylint==1.4.0',
        'pytest==2.6.4',
        'simplejson==3.6.5',
        'six==1.8.0',
        'unittest2==0.8.0',
        'wheel==0.24.0',
        ''
    ))

    between()

    enable_coverage(tmpdir)
    # there may be more or less packages depending on what exactly happened between
    assert 'cov-core==1.15.0\ncoverage==4.0a1\n' in pip_freeze()

    start = time()
    # second install should also need no network access
    # these are arbitrary invalid IP's
    venv_update(
        http_proxy='http://300.10.20.30:40',
        https_proxy='http://400.11.22.33:44',
        ftp_proxy='http://500.4.3.2:1',
    )
    time2 = time() - start
    assert pip_freeze() == '\n'.join((
        'PyYAML==3.11',
        'argparse==1.2.1',
        'astroid==1.3.2',
        'chroniker==0.0.0',
        'logilab-common==0.63.2',
        'py==1.4.26',
        'pylint==1.4.0',
        'pytest==2.6.4',
        'simplejson==3.6.5',
        'six==1.8.0',
        'unittest2==0.8.0',
        'wheel==0.24.0',
        ''
    ))

    # second install should be at least twice as fast
    ratio = time1 / time2
    print('%.2fx speedup' % ratio)
    return ratio


@pytest.mark.flaky(reruns=2)
def test_noop_install_faster(tmpdir):
    def do_nothing():
        pass

    # constrain both ends, to show that we know what's going on
    # performance log: (clear when numbers become invalidated)
    #   2014-12-22 travis py26: 9.4-12
    #   2014-12-22 travis py27: 10-13
    #   2014-12-22 travis py34: 6-14
    #   2014-12-22 travis pypy: 5.5-7.5
    assert 5 < install_twice(tmpdir, between=do_nothing) < 14


@pytest.mark.flaky(reruns=2)
def test_cached_clean_install_faster(tmpdir):
    def clean():
        venv = tmpdir.join('virtualenv_run')
        assert venv.isdir()
        venv.remove()
        assert not venv.exists()

    # I get ~4x locally, but only 2.5x on travis
    # constrain both ends, to show that we know what's going on
    # performance log: (clear when numbers become invalidated)
    #   2014-12-22 travis py26: 4-6
    #   2014-12-22 travis py27: 3.2-5.5
    #   2014-12-22 travis py34: 3.7-6
    #   2014-12-22 travis pypy: 3.5-4
    #   2014-12-24 travis pypy: 2.9-3.5
    #   2014-12-24 osx pypy: 3.9
    assert 2.5 < install_twice(tmpdir, between=clean) < 7


def test_arguments_version(tmpdir):
    """Show that we can pass arguments through to virtualenv"""
    tmpdir.chdir()

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        # should show virtualenv version, then crash
        venv_update('--version')

    assert excinfo.value.returncode == 1
    out, err = excinfo.value.result
    lasterr = err.rsplit('\n', 2)[-2]
    assert lasterr.startswith('virtualenv executable not found: /'), err
    assert lasterr.endswith('/virtualenv_run/bin/python'), err

    lines = [uncolor(line) for line in out.split('\n')]
    assert len(lines) == 3, lines
    assert lines[0].endswith(' -m virtualenv virtualenv_run --version'), repr(lines[0])


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


def pip(*args):
    # because the scripts are made relative, it won't use the venv python without being explicit.
    return run('virtualenv_run/bin/python', 'virtualenv_run/bin/pip', *args)


def pip_freeze():
    out, err = pip('freeze', '--local')

    assert err == ''
    return out


def test_update_while_active(tmpdir):
    tmpdir.chdir()
    requirements('virtualenv<2')

    venv_update()
    assert 'mccabe' not in pip_freeze()

    # An arbitrary small package: mccabe
    requirements('virtualenv<2\nmccabe')

    venv_update_symlink_pwd()
    run('sh', '-c', '. virtualenv_run/bin/activate && python venv_update.py')
    assert 'mccabe' in pip_freeze()


def test_eggless_url(tmpdir):
    tmpdir.chdir()
    requirements('')

    venv_update()
    assert 'venv-update' not in pip_freeze()

    # An arbitrary git-url requirement.
    requirements('git+git://github.com/Yelp/venv-update.git')

    venv_update()
    assert 'venv-update' in pip_freeze()


def test_scripts_left_behind(tmpdir):
    tmpdir.chdir()
    requirements('')

    venv_update()

    # an arbitrary small package with a script: pep8
    script_path = Path('virtualenv_run/bin/pep8')
    assert not script_path.exists()

    pip('install', 'pep8')
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

    assert excinfo.value.returncode == 1
    assert firstreq.mtime() > Path('virtualenv_run').mtime()

    # blank requirements should succeed
    lastreq.write('')

    venv_update('virtualenv_run', *reqs)
    assert Path(reqs[0]).mtime() < Path('virtualenv_run').mtime()


def test_timestamps_single(tmpdir):
    tmpdir.chdir()
    requirements('')
    assert_timestamps('requirements.txt')


def test_timestamps_multiple(tmpdir):
    tmpdir.chdir()
    requirements('')
    Path('requirements2.txt').write('')
    assert_timestamps('requirements.txt', 'requirements2.txt')


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
    from testing.capture_subprocess import read_all
    close(write)
    result = read_all(read)
    vupdate.wait()

    result = result.decode('US-ASCII')
    uncolored = uncolor(result)
    assert uncolored.startswith('> ')
    assert uncolored.endswith('''\
virtualenv virtualenv_run --version
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

    assert excinfo.value.returncode == 1
    _, err = excinfo.value.result
    lasterr = strip_coverage_warnings(err).rsplit('\n', 2)[-2]
    errname = 'NotADirectoryError' if PY33 else 'OSError'
    assert lasterr.startswith(errname + ': [Errno 20] Not a directory'), err

    assert Path('requirements.txt').isfile()
    assert Path('requirements.txt').read() == ''
    assert not Path('myvenv').exists()
