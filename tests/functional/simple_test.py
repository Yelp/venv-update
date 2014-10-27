from __future__ import print_function
from __future__ import unicode_literals
from py._path.local import LocalPath as Path
import pytest

TOP = Path(__file__) / '../../..'
SCENARIOS = TOP/'tests/scenarios'

from sys import version_info
PY33 = (version_info >= (3, 3))


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

# coverage.py adds some helpful warnings to stderr, with no way to quiet them.
from re import compile as Regex, MULTILINE
coverage_warnings_regex = Regex(
    r'^Coverage.py warning: (Module .* was never imported\.|No data was collected\.)\n',
    flags=MULTILINE,
)


def strip_coverage_warnings(stderr):
    return coverage_warnings_regex.sub('', stderr)


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
        requirements.write('''\
simplejson
pyyaml
coverage
pylint
pytest
''')

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
    assert ratio > 2


def test_arguments_version(tmpdir, capfd):
    """Show that we can pass arguments through to virtualenv"""

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        # should show virtualenv version, then crash
        do_install(tmpdir, '--version')

    assert excinfo.value.returncode == 1
    out, err = capfd.readouterr()
    lasterr = strip_coverage_warnings(err).rsplit('\n', 2)[-2]
    if PY33:
        errname = 'FileNotFoundError'
    else:
        errname = 'IOError'
    assert lasterr.startswith(errname + ': [Errno 2] No such file or directory:')
    assert lasterr.endswith("/activate_this.py'")

    out = out.split('\n')
    assert out[-3].endswith('/virtualenv virtualenv_run --version')


def test_arguments_system_packages(tmpdir, capfd):
    """Show that we can pass arguments through to virtualenv"""
    tmpdir.chdir()
    run('rsync', '-a', str(SCENARIOS) + '/trivial/', '.')
    do_install(tmpdir, '--system-site-packages')
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


def test_update_while_active(tmpdir, capfd):
    tmpdir.chdir()
    run('rsync', '-a', str(SCENARIOS) + '/trivial/', '.')

    do_install(tmpdir)
    run('virtualenv_run/bin/pip', 'freeze')
    out, err = capfd.readouterr()

    assert strip_coverage_warnings(err) == ''
    assert 'mccabe' not in out

    with open('requirements.txt', 'w') as requirements:
        # An arbitrary small package: mccabe
        requirements.write('mccabe')
