from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from testing import enable_coverage
from testing import pip_freeze
from testing import requirements
from testing import venv_update
from venv_update import __version__


@pytest.mark.usefixtures('pypi_server')
def test_bad_symlink_can_be_fixed(tmpdir):
    """If the symlink at ~/.config/venv-update/$version/venv-update is wrong,
    we should be able to fix it and keep going.

    https://github.com/Yelp/pip-faster/issues/98
    """
    tmpdir.chdir()

    scratch_dir = tmpdir.join('home', '.cache').ensure_dir('venv-update').ensure_dir(__version__)
    symlink = scratch_dir.join('venv-update')

    # run a trivial venv-update to populate the cache and create a proper symlink
    assert not symlink.exists()
    requirements('')
    venv_update()
    assert symlink.exists()

    # break the symlink by hand (in real life, this can happen if mounting
    # things into Docker containers, for example)
    symlink.remove()
    symlink.mksymlinkto('/nonexist')
    assert not symlink.exists()

    # a simple venv-update should install packages and fix the symlink
    enable_coverage(tmpdir)
    requirements('pure-python-package')
    venv_update()
    assert '\npure-python-package==0.2.0\n' in pip_freeze()
    assert symlink.exists()


@pytest.mark.usefixtures('pypi_server')
def test_symlink_is_relative(tmpdir):
    """We want to be able to mount ~/.cache/venv-update in different locations
    safely, so the symlink must be relative.

    https://github.com/Yelp/pip-faster/issues/101
    """
    tmpdir.chdir()

    scratch_dir = tmpdir.join('home', '.cache').ensure_dir('venv-update').ensure_dir(__version__)
    symlink = scratch_dir.join('venv-update')

    # run a trivial venv-update to populate the cache and create a proper symlink
    assert not symlink.exists()
    requirements('')
    venv_update()

    # it should be a valid, relative symlink
    assert symlink.exists()
    assert not symlink.readlink().startswith('/')

    # and if we move the entire scratch directory, the symlink should still be valid
    # (this is what we really care about)
    scratch_dir.move(tmpdir.join('derp'))
    symlink = tmpdir.join('derp', 'venv-update')
    assert symlink.exists()
