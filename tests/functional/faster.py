"""attempt to show that pip-faster is... faster"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import contextlib

import pytest
from py._path.local import LocalPath as Path

from testing import enable_coverage
from testing import install_coverage
from testing import pip_freeze
from testing import requirements
from testing import venv_update
from venv_update import __version__


def time_savings(tmpdir, between):
    """install twice, and the second one should be faster, due to whl caching"""
    with tmpdir.as_cwd():
        enable_coverage()

        @contextlib.contextmanager
        def venv_setup():
            # First just set up a blank virtualenv, this'll bypass the
            # bootstrap when we're actually testing for speed
            if not Path('venv').exists():
                requirements('')
                venv_update()
            install_coverage()

            # Now the actual requirements we'll install
            requirements('\n'.join((
                'project_with_c',
                'pure_python_package==0.2.1',
                'slow_python_package==0.1.0',
                'dependant_package',
                'many_versions_package>=2,<3',
                ''
            )))

            yield

            expected = '\n'.join((
                'appdirs==1.4.3',
                'dependant-package==1',
                'implicit-dependency==1',
                'many-versions-package==2.1',
                'packaging==16.8',
                'pip==9.0.1',
                'project-with-c==0.1.0',
                'pure-python-package==0.2.1',
                'pyparsing==2.2.0',
                'setuptools==35.0.2',
                'six==1.10.0',
                'slow-python-package==0.1.0',
                'venv-update==%s' % __version__,
                'wheel==0.29.0',
                ''
            ))
            assert pip_freeze() == expected

        from time import time

        with venv_setup():
            start = time()
            venv_update(
                PIP_VERBOSE='1',
                PIP_RETRIES='0',
                PIP_TIMEOUT='0',
            )
            time1 = time() - start

        between()

        with venv_setup():
            start = time()
            # second install should also need no network access
            # these are localhost addresses with arbitrary invalid ports
            venv_update(
                PIP_VERBOSE='1',
                PIP_RETRIES='0',
                PIP_TIMEOUT='0',
                http_proxy='http://127.0.0.1:111111',
                https_proxy='https://127.0.0.1:222222',
                ftp_proxy='ftp://127.0.0.1:333333',
            )
            time2 = time() - start

        print()
        print('%.3fs originally' % time1)
        print('%.3fs subsequently' % time2)

        difference = time1 - time2
        print('%.2fs speedup' % difference)

        ratio = time1 / time2
        percent = (ratio - 1) * 100
        print('%.2f%% speedup' % percent)
        return difference


@pytest.mark.usefixtures('pypi_server')
def test_noop_install_faster(tmpdir):
    def do_nothing():
        pass

    # the slow-python-package takes five seconds to compile
    assert time_savings(tmpdir, between=do_nothing) > 6


@pytest.mark.usefixtures('pypi_server_with_fallback', 'pypi_packages')
def test_cached_clean_install_faster(tmpdir):
    def clean():
        venv = tmpdir.join('venv')
        assert venv.isdir()
        venv.remove()
        assert not venv.exists()

    # the slow-python-package takes five seconds to compile
    assert time_savings(tmpdir, between=clean) > 5
