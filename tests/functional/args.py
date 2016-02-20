from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from testing import strip_coverage_warnings
from testing import venv_update
from venv_update import __doc__ as HELP_OUTPUT
from venv_update import __version__ as VERSION


def test_help():
    assert HELP_OUTPUT
    assert HELP_OUTPUT.startswith('usage:')
    last_line = HELP_OUTPUT.rsplit('\n', 2)[-2].strip()
    assert last_line.startswith('Please send issues to: https://')

    out, err = venv_update('--help')
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT

    out, err = venv_update('-h')
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT


def test_version():
    assert VERSION

    out, err = venv_update('--version')
    assert strip_coverage_warnings(err) == ''
    assert out == VERSION + '\n'

    out, err = venv_update('-V')
    assert strip_coverage_warnings(err) == ''
    assert out == VERSION + '\n'


def test_bad_option():
    import pytest
    from subprocess import CalledProcessError

    with pytest.raises(CalledProcessError) as excinfo:
        venv_update('venv')
    out, err = excinfo.value.result
    assert strip_coverage_warnings(err) == '''\
invalid option: venv
Try --help for more information.
'''
    assert out == ''
