from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest
from testing import Path
from testing import requirements
from testing import run
from testing import venv_update


@pytest.mark.usefixtures('pypi_server')
def test_relocatable(tmpdir):
    tmpdir.chdir()
    requirements('')
    venv_update('--python=python')  # this makes pypy work right. derp.

    Path('virtualenv_run').rename('relocated')

    python = 'relocated/bin/python'
    assert Path(python).exists()
    run(python, '-m', 'pip.__main__', '--version')
