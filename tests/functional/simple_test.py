from __future__ import print_function
from __future__ import unicode_literals
from py._path.local import LocalPath as Path
import pytest

TOP = Path(__file__) / '../../..'
SCENARIOS = TOP/'tests/scenarios'


def run(*cmd, **env):
    from subprocess import check_call

    if env:
        from os import environ
        tmp = env
        env = environ.copy()
        env.update(tmp)
    else:
        env = None

    check_call(cmd, env=env)


def do_install(tmpdir, *args):
    # we get coverage for free via the (patched) pytest-cov plugin
    run(
        'venv-update',
        *args,
        HOME=str(tmpdir)
    )


def test_trivial(tmpdir):
    tmpdir.chdir()

    # Trailing slash is essential to rsync
    run('rsync', '-a', str(SCENARIOS) + '/trivial/', '.')
    do_install(tmpdir)


@pytest.mark.flaky(reruns=10)
def test_second_install_faster(tmpdir):
    """install twice, and the second one should be faster, due to whl caching"""
    tmpdir.chdir()

    # Trailing slash is essential to rsync
    run('rsync', '-a', str(SCENARIOS) + '/trivial/', '.')
    with open('requirements.txt', 'w') as requirements:
        # An arbitrary package that takes a bit of time to install: twisted
        # Should I make my own fake c-extention just to remove this dependency?
        requirements.write('twisted')

    from time import time
    start = time()
    do_install(tmpdir)
    time1 = time() - start

    start = time()
    do_install(tmpdir)
    time2 = time() - start

    # second install should be at least twice as fast
    ratio = time1 / time2
    print('%.1fx speedup' % ratio)
    assert ratio / 2


def test_arguments_version(tmpdir, capfd):
    """Show that we can pass arguments through to virtualenv"""

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        # should show virtualenv version, then crash
        do_install(tmpdir, '--version')

    assert excinfo.value.returncode == 1
    out, err = capfd.readouterr()
    lasterr = err.rsplit('\n', 2)[-2]
    assert lasterr.startswith('IOError: [Errno 2] No such file or directory:')
    assert lasterr.endswith("/activate_this.py'")

    out = out.split('\n')
    assert out[-3].endswith('/virtualenv virtualenv_run --version')


def test_arguments_system_packages(tmpdir, capfd):
    """Show that we can pass arguments through to virtualenv"""
    tmpdir.chdir()
    run('rsync', '-a', str(SCENARIOS) + '/trivial/', '.')
    do_install(tmpdir, '--system-site-packages')
    out, err = capfd.readouterr()  # flush buffers

    run(str(tmpdir.join('virtualenv_run', 'bin', 'python')), '-c', '''\
import sys
for p in sys.path:
    if p.startswith(sys.real_prefix) and p.endswith("site-packages"):
        print p
''')
    out, err = capfd.readouterr()
    assert err == ''
    out = out.rstrip('\n')
    assert out and Path(out).isdir()
