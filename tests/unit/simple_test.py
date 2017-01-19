from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

import pip_faster
import venv_update
from testing import Path


def test_importable():
    assert venv_update


def test_pip_get_installed():
    installed = pip_faster.pip_get_installed()
    installed = pip_faster.reqnames(installed)
    installed = sorted(installed)
    print(installed)
    assert 'pip' in installed


@pytest.mark.parametrize('filename,expected', [
    ('foo.py', 'foo.py'),
    ('foo.pyc', 'foo.py'),
    ('foo.pye', 'foo.pye'),
    ('../foo.pyc', '../foo.py'),
    ('/a/b/c/foo.pyc', '/a/b/c/foo.py'),
    ('bar.pyd', 'bar.py'),
    ('baz.pyo', 'baz.py'),
])
def test_dotpy(filename, expected):
    assert venv_update.dotpy(filename) == expected


@pytest.mark.parametrize('args', [
    ('-h',),
    ('a', '-h',),
    ('-h', 'b'),
    ('--help',),
    ('a', '--help',),
    ('--help', 'b'),
])
def test_parseargs_help(args, capsys):
    from venv_update import __doc__ as HELP_OUTPUT
    with pytest.raises(SystemExit) as excinfo:
        assert venv_update.parseargs(args)

    out, err = capsys.readouterr()
    assert err == ''
    assert out == HELP_OUTPUT
    assert excinfo.value.code == 0


@pytest.mark.parametrize('args,expected', [
    (
        ('1', 'foo'),
        '1 foo',
    ), (
        ('1 foo',),
        "'1 foo'",
    ), (
        (r'''she said "hi", she said 'bye' ''',),
        r"""'she said "hi", she said '"'"'bye'"'"' '""",
    ),
])
def test_shellescape(args, expected):
    assert venv_update.shellescape(args) == expected


@pytest.mark.parametrize('path,expected', [
    (
        '1',
        '1',
    ), (
        '2 foo',
        "'2 foo'",
    ), (
        '../foo',
        '../foo',
    ),
])
def test_shellescape_relpath(path, expected, tmpdir):
    tmpdir.chdir()
    tmpfile = tmpdir.join(path)
    args = (tmpfile.strpath,)
    assert venv_update.shellescape(args) == expected
    assert expected != tmpfile.strpath


def test_shellescape_relpath_longer(tmpdir):
    tmpdir.chdir()
    path = Path('/a/b')
    args = (path.strpath,)
    assert venv_update.shellescape(args) == path.strpath


@pytest.mark.parametrize('req,expected', [
    ('foo', False),
    ('foo==1', True),
    ('bar<3,==2,>1', True),
    ('quux<3,!=2,>1', False),
    ('wat==2,!=2', True),
    ('wat-more==2,==3', True),
])
def test_is_req_pinned(req, expected):
    from pkg_resources import Requirement
    req = Requirement.parse(req)
    assert pip_faster.is_req_pinned(req) is expected


def test_is_req_pinned_null():
    assert pip_faster.is_req_pinned(None) is False


def test_wait_for_all_subprocesses(monkeypatch):
    class _nonlocal(object):
        wait = 10
        thrown = False

    def fakewait():
        if _nonlocal.wait <= 0:
            _nonlocal.thrown = True
            raise OSError(10, 'No child process')
        else:
            _nonlocal.wait -= 1

    import os
    monkeypatch.setattr(os, 'wait', fakewait)
    venv_update.wait_for_all_subprocesses()

    assert _nonlocal.wait == 0
    assert _nonlocal.thrown is True


def test_samefile(tmpdir):
    with tmpdir.as_cwd():
        a = tmpdir.ensure('a')
        b = tmpdir.ensure('b')
        tmpdir.join('c').mksymlinkto(a, absolute=True)
        tmpdir.join('d').mksymlinkto(b, absolute=False)

        assert venv_update.samefile('a', 'b') is False
        assert venv_update.samefile('a', 'x') is False
        assert venv_update.samefile('x', 'a') is False

        assert venv_update.samefile('a', 'a') is True
        assert venv_update.samefile('a', 'c') is True
        assert venv_update.samefile('d', 'b') is True


def passwd():
    import os
    import pwd
    return pwd.getpwuid(os.getuid())


def test_user_cache_dir():
    assert venv_update.user_cache_dir() == passwd().pw_dir + '/.cache'

    from os import environ
    environ['HOME'] = '/foo/bar'
    assert venv_update.user_cache_dir() == '/foo/bar/.cache'

    environ['XDG_CACHE_HOME'] = '/quux/bar'
    assert venv_update.user_cache_dir() == '/quux/bar'


def test_get_python_version():
    import sys

    expected = '.'.join(str(part) for part in sys.version_info[:3])
    actual = venv_update.get_python_version(sys.executable)
    assert actual.startswith(expected)
    assert actual[len(expected)] in ' +'

    assert venv_update.get_python_version('total garbage') is None

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        venv_update.get_python_version('/bin/false')
    assert excinfo.value.returncode == 1
