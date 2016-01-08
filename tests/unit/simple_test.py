from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

import pip_faster
import venv_update
from testing import Path


def test_importable():
    assert venv_update


def test_parse_reqs(tmpdir):
    tmpdir.chdir()

    with open('setup.py', 'w') as setup:
        setup.write('\n')

    with open('reqs.txt', 'w') as reqs:
        reqs.write('''\
.

-r reqs2.txt
# a comment here
mccabe

pep8==1.0

-e hg+https://bitbucket.org/bukzor/coverage.py@__main__-support#egg=aweirdname
-e git+git://github.com/bukzor/cov-core.git@master#egg=cov-core
hg+https://bitbucket.org/logilab/pylint@58c66aa083777059a2e6b46f6a0545a2f4977097

file:///my/random/project
-e file:///my/random/project2
''')

    with open('reqs2.txt', 'w') as reqs:
        reqs.write('''\
pep8''')

    # show that ordering is preserved in the parse
    parsed = pip_faster.pip_parse_requirements(('reqs.txt',))
    assert [
        (req.name, req.url)
        for req in parsed
    ] == [
        (None, 'file://' + tmpdir.strpath),
        ('pep8', None),
        ('mccabe', None),
        ('pep8', None),
        ('aweirdname', 'hg+https://bitbucket.org/bukzor/coverage.py@__main__-support#egg=aweirdname'),
        ('cov-core', 'git+git://github.com/bukzor/cov-core.git@master#egg=cov-core'),
        (None, 'hg+https://bitbucket.org/logilab/pylint@58c66aa083777059a2e6b46f6a0545a2f4977097'),
        (None, 'file:///my/random/project'),
        (None, 'file:///my/random/project2'),
    ]


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


@pytest.mark.parametrize('args,expected', [
    (
        (),
        ('venv', ('requirements.txt',), ()),
    ), (
        ('a',),
        ('a', ('requirements.txt',), ())
    ), (
        ('a', 'b'),
        ('a', ('b',), ())
    ), (
        ('a', 'b', 'c'),
        ('a', ('b', 'c'), ())
    ), (
        ('a', 'b', 'c', 'd'),
        ('a', ('b', 'c', 'd'), ())
    ), (
        ('a', '--opt', 'optval', 'b', 'c', 'd'),
        ('a', ('optval', 'b', 'c', 'd'), ('--opt',))
    ), (
        ('a', '--opt', 'optval', 'b', '--opt2', 'c', 'd'),
        ('a', ('optval', 'b', 'c', 'd'), ('--opt', '--opt2'))
    ), (
        ('--opt2', 'a', '--opt', 'optval', 'b', '--opt2', 'c', 'd'),
        ('a', ('optval', 'b', 'c', 'd'), ('--opt2', '--opt', '--opt2'))
    ),
])
def test_parseargs(args, expected):
    assert venv_update.parseargs(args) == expected


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
    (
        'foo',
        False,
    ), (
        'foo==1',
        True,
    ), (
        'bar<3,==2,>1',
        True,
    ), (
        'quux<3,!=2,>1',
        False,
    ), (
        'wat==2,!=2',
        True,
    ), (
        'wat-more==2,==3',
        True,
    )
])
def test_req_is_absolute(req, expected):
    from pkg_resources import Requirement
    req = Requirement.parse(req)
    assert pip_faster.req_is_absolute(req) is expected


def test_req_is_absolute_null():
    assert pip_faster.req_is_absolute(None) is False


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
