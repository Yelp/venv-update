from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from testing import enable_coverage
from testing import pip_freeze
from testing import run
from venv_update import __version__


@pytest.mark.usefixtures('pypi_server')
def test_circular_dependencies(tmpdir):
    """pip-faster should be able to install packages with circular
    dependencies."""
    tmpdir.chdir()
    venv = enable_coverage(tmpdir, 'venv')

    pip = venv.join('bin/pip').strpath
    run(pip, 'install', 'pip-faster==' + __version__)

    run(
        venv.join('bin/pip-faster').strpath,
        'install',
        'circular-dep-a',
    )

    frozen_requirements = pip_freeze(str(venv)).split('\n')
    assert 'circular-dep-a==1.0' in frozen_requirements
    assert 'circular-dep-b==1.0' in frozen_requirements
