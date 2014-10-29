from testing import strip_coverage_warnings, venv_update
from venv_update import HELP_OUTPUT


def test_help(capfd):
    assert HELP_OUTPUT

    venv_update('--help')
    out, err = capfd.readouterr()
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT

    venv_update('-h')
    out, err = capfd.readouterr()
    assert strip_coverage_warnings(err) == ''
    assert out == HELP_OUTPUT
