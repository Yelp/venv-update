from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals


def test_cli():
    from venv_update import check_output
    from sys import executable
    from testing.python_lib import __file__ as script
    output = check_output((executable, script))
    output = output.splitlines()
    assert len(output) == 1
    output = output[0]
    assert output.endswith('site-packages')

    from testing import Path
    import sys
    path = Path(sys.prefix).join(output)
    assert path.basename == 'site-packages'
    assert path.check(dir=True)
