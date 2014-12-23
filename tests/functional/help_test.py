from testing import strip_coverage_warnings, venv_update
from venv_update import __doc__ as HELP_OUTPUT


def test_help():
    assert HELP_OUTPUT
    assert HELP_OUTPUT.startswith('usage:')
    last_line = HELP_OUTPUT.rsplit('\n', 2)[-2].strip()
    assert last_line.startswith('Version control at: http')

    out, err = venv_update('--help')
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT

    out, err = venv_update('-h')
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT
