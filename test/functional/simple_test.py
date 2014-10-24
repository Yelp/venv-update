from __future__ import print_function
from __future__ import unicode_literals
from py._path.local import LocalPath as Path
import pytest

TOP = Path(__file__) / '../../..'
SCENARIOS = TOP/'test/scenarios'


def run(cmd, *args, **env):
    from pipes import quote
    from subprocess import check_call

    cmd += args
    if env:
        from os import environ
        tmp = env
        env = environ.copy()
        env.update(tmp)
    else:
        env = None

    check_call(('echo', '\033[01;36m>\033[m \033[01;33m{0}\033[m'.format(
        ' '.join(quote(arg) for arg in cmd)
    )))
    check_call(cmd, env=env)


def do_install(tmpdir, *args):
    # we get coverage for free via the (patched) pytest-cov plugin
    run(
        ('venv-update',) + args,
        HOME=str(tmpdir),
    )


def test_trivial(tmpdir):
    tmpdir.chdir()

    # Trailing slash is essential to rsync
    run(('rsync', '-a', str(SCENARIOS) + '/trivial/', '.'))
    do_install(tmpdir)


# Not yet installed: https://github.com/klrmn/pytest-rerunfailures
@pytest.mark.flaky(reruns=10)
def test_second_install_faster(tmpdir):
    """install twice, and the second one should be faster, due to whl caching"""
    tmpdir.chdir()

    # Trailing slash is essential to rsync
    run(('rsync', '-a', str(SCENARIOS) + '/trivial/', '.'))
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


def test_arguments():
    pass  # TODO: anything
