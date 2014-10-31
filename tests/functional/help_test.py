from testing import strip_coverage_warnings, venv_update
from venv_update import __doc__ as HELP_OUTPUT


def test_help(capfd):
    assert HELP_OUTPUT
    assert HELP_OUTPUT.startswith('usage:')
    last_line = HELP_OUTPUT.rsplit('\n', 2)[-2].strip()
    assert last_line.startswith('-h, --help ')

    venv_update('--help')
    out, err = capfd.readouterr()
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT

    venv_update('-h')
    out, err = capfd.readouterr()
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT
