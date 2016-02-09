from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from testing import strip_coverage_warnings
from testing import venv_update
from venv_update import __doc__ as HELP_OUTPUT
from venv_update import __version__


def test_help():
    assert HELP_OUTPUT
    assert HELP_OUTPUT.startswith('usage:')
    last_line = HELP_OUTPUT.rsplit('\n', 2)[-2].strip()
    assert last_line.startswith('Version control and more details: http')

    out, err = venv_update('--help')
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT

    out, err = venv_update('-h')
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT


def test_version():
    """venv_update should print version when requested."""
    expected_version_out = 'venv-update v{0}\n'.format(__version__)

    out, err = venv_update('--version')
    assert strip_coverage_warnings(err) == ''
    assert out == expected_version_out

    out, err = venv_update('-V')
    assert strip_coverage_warnings(err) == ''
    assert out == expected_version_out
