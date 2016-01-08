"""attempt to show that pip-faster is... faster"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from testing import enable_coverage
from testing import pip_freeze
from testing import requirements
from testing import TOP
from testing import venv_update
from venv_update import __version__


def time_savings(tmpdir, between):
    """install twice, and the second one should be faster, due to whl caching"""
    with tmpdir.as_cwd():

        requirements('\n'.join((
            'project_with_c',
            'pure_python_package==0.2.0',
            'slow_python_package==0.1.0',
            'dependant_package',
            'many_versions_package>=2,<3',
            '-r %s/requirements.d/coverage.txt' % TOP,
            ''
        )))

        from time import time

        start = time()
        venv_update(
            PIP_VERBOSE='1',
        )
        time1 = time() - start
        expected = '\n'.join((
            'coverage==4.0.3',
            'coverage-enable-subprocess==0',
            'dependant-package==1',
            'implicit-dependency==1',
            'many-versions-package==2.1',
            'pip-faster==%s' % __version__,
            'project-with-c==0.1.0',
            'pure-python-package==0.2.0',
            'slow-python-package==0.1.0',
            'virtualenv==1.11.6',
            'wheel==0.26.0',
            ''
        ))
        assert pip_freeze() == expected

        between()

        start = time()
        # second install should also need no network access
        # these are localhost addresses with arbitrary invalid ports
        venv_update(
            PIP_VERBOSE='1',
            http_proxy='http://127.0.0.1:111111',
            https_proxy='https://127.0.0.1:222222',
            ftp_proxy='ftp://127.0.0.1:333333',
        )
        time2 = time() - start
        assert pip_freeze() == expected

        print()
        print('%.3fs originally' % time1)
        print('%.3fs subsequently' % time2)

        difference = time1 - time2
        print('%.2fs speedup' % difference)

        ratio = time1 / time2
        percent = (ratio - 1) % 100
        print('%.2f%% speedup' % percent)
        return difference


@pytest.mark.usefixtures('pypi_server')
def test_noop_install_faster(tmpdir):
    def do_nothing():
        pass

    # the slow-python-package takes five seconds to compile
    assert time_savings(tmpdir, between=do_nothing) > 6


@pytest.mark.usefixtures('pypi_server_with_fallback')
def test_cached_clean_install_faster(tmpdir, pypi_packages):
    def clean():
        venv = tmpdir.join('venv')
        assert venv.isdir()
        venv.remove()
        assert not venv.exists()
        enable_coverage(tmpdir)

        # copy the bootstrap-essential wheels to the wheelhouse where they can be found.
        # FIXME: pip7 has the behavior we want: wheel anything we install
        from glob import glob

        for package in (
                'argparse',
                'pip',
                'pip_faster',
                'virtualenv',
                'wheel',
        ):
            pattern = str(pypi_packages.join(package + '-*.whl'))
            wheel = glob(pattern)
            assert len(wheel) == 1, (pattern, wheel)
            wheel = wheel[0]

            from shutil import copy
            copy(wheel, str(tmpdir.join('home/.cache/pip-faster/wheelhouse')))

    # the slow-python-package takes five seconds to compile
    assert time_savings(tmpdir, between=clean) > 5
