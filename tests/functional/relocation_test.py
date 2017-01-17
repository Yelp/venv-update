from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from testing import install_coverage
from testing import Path
from testing import requirements
from testing import run
from testing import venv_update


@pytest.mark.usefixtures('pypi_server')
def test_relocatable(tmpdir):
    tmpdir.chdir()
    requirements('')
    venv_update()

    Path('venv').rename('relocated')

    python = 'relocated/bin/python'
    assert Path(python).exists()
    run(python, '-m', 'pip.__main__', '--version')


@pytest.mark.usefixtures('pypi_packages')
def test_relocatable_cache(tmpdir, pypi_server):
    tmpdir.chdir()
    requirements('pure-python-package==0.2.1')
    venv_update()
    path_rest = (
        '.cache', 'pip-faster', 'wheelhouse', pypi_server, 'simple',
        'pure-python-package',
        'pure_python_package-0.2.1-py2.py3-none-any.whl',
    )
    assert tmpdir.join('home', *path_rest).exists()
    tmpdir.join('home').rename('home2')
    assert tmpdir.join('home2', *path_rest).exists()


@pytest.mark.usefixtures('pypi_server', 'pypi_packages')
def test_pip_cache_goes_missing_still_installable(tmpdir):
    tmpdir.chdir()
    requirements('pure-python-package==0.2.1')
    venv_update()
    tmpdir.join('venv').remove()

    # This breaks the symlinks in our cache
    pip_cache = tmpdir.join('home', '.cache', 'pip')
    assert pip_cache.exists()
    pip_cache.remove()

    install_coverage()
    venv_update()
