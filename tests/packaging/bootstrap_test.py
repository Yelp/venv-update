from os import environ

from clom import clom

TOP = environ.get('TOP', '.')


def it_is_built():
    """Show that re-building the bootstrap doesn't cause any diff."""
    for cmd in (
            clom[TOP + '/bootstrap/make.py'],
            clom.git.status('-s', 'bootstrap/result.py'),
    ):
        result = cmd.shell()
        assert result.code == 0
        assert result.stderr == ''
        assert result.stdout == ''
