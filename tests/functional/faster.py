"""attempt to show that pip-faster is... faster"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pytest
from testing import requirements
from testing import TOP
from testing import venv_update
from testing import pip_freeze
from testing import enable_coverage


def install_twice(tmpdir, between):
    """install twice, and the second one should be faster, due to whl caching"""
    tmpdir.chdir()

    # Arbitrary packages that takes a bit of time to install:
    # Should I make a fixture c-extension to remove these dependencies?
    # NOTE: Avoid projects that use 2to3 (urwid). It makes the runtime vary too widely.
    requirements('''\
project_with_c
pure_python_package
slow_python_package
dependant_package
many_versions_package>=2,<3
''')

    from time import time
    enable_coverage(tmpdir)

    start = time()
    venv_update()
    time1 = time() - start
    expected = '\n'.join((
        'dependant-package==1',
        'implicit-dependency==1',
        'many-versions-package==2.1',
        'pip-faster==0.1.4.4',
        'project-with-c==0.1.0',
        'pure-python-package==0.2.0',
        'slow-python-package==0.1.0',
        'virtualenv==1.11.6',
        'wheel==0.26.0',
        ''
    ))
    assert pip_freeze() == expected

    between()

    # FIXME: pip7 has the behavior we want: wheel anything we install
    from glob import glob

    for package in (
            'argparse',
            'pip',
            'pip_faster',
            'virtualenv',
            'wheel',
    ):
        pattern = str(TOP.join('build/packages', package + '-*.whl'))
        wheel = glob(pattern)
        assert len(wheel) == 1, (pattern, wheel)
        wheel = wheel[0]

        from shutil import copy
        copy(wheel, str(tmpdir.join('.pip/wheelhouse')))

    start = time()
    # second install should also need no network access
    # these are localhost addresses with arbitrary invalid ports
    venv_update(
        http_proxy='http://127.0.0.1:111111',
        https_proxy='https://127.0.0.1:222222',
        ftp_proxy='ftp://127.0.0.1:333333',
    )
    time2 = time() - start
    assert pip_freeze() == expected

    # second install should be at least twice as fast
    ratio = time1 / time2
    print('%.2fx speedup' % ratio)
    return ratio


@pytest.mark.usefixtures('pypi_server')
def test_noop_install_faster(tmpdir):
    def do_nothing():
        pass

    # constrain both ends, to show that we know what's going on
    # performance log: (clear when numbers become invalidated)
    #   2015-11-19 linux py27: 12.21 - 13.14
    assert 11 < install_twice(tmpdir, between=do_nothing) < 14


@pytest.mark.usefixtures('pypi_server_with_fallback')
def test_cached_clean_install_faster(tmpdir):
    def clean():
        venv = tmpdir.join('virtualenv_run')
        assert venv.isdir()
        venv.remove()
        assert not venv.exists()

    # I get ~4x locally, but only 2.5x on travis
    # constrain both ends, to show that we know what's going on
    # performance log: (clear when numbers become invalidated)
    #   2015-11-19 linux py27: 4.00 - 4.22
    assert 3 < install_twice(tmpdir, between=clean) < 5
