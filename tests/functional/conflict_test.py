from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
from subprocess import CalledProcessError

import pytest

import testing as T
from testing.python_lib import PYTHON_LIB


def assert_venv_marked_invalid(venv):
    """we mark a virtualenv as invalid by bumping its timestamp back by a day"""
    venv_age = time.time() - os.path.getmtime(venv.strpath)
    assert venv_age / 60 / 60 / 24 > 1


@pytest.mark.usefixtures('pypi_server')
def test_conflicting_reqs(tmpdir):
    tmpdir.chdir()
    T.requirements('''
dependant_package
conflicting_package
''')

    with pytest.raises(CalledProcessError) as excinfo:
        T.venv_update()
    assert excinfo.value.returncode == 1
    out, err = excinfo.value.result

    err = T.strip_coverage_warnings(err)
    assert err == ''

    out = T.uncolor(out)
    assert (
        '''
Cleaning up...
Error: version conflict: many-versions-package 3 (virtualenv_run/%s)'''
        ''' <-> many-versions-package<2 (from conflicting-package (from -r requirements.txt (line 3)))
Storing debug log for failure in %s/home/.pip/pip.log

Something went wrong! Sending 'virtualenv_run' back in time, so make knows it's invalid.
''' % (PYTHON_LIB, tmpdir)
    ) in out

    assert_venv_marked_invalid(tmpdir.join('virtualenv_run'))


@pytest.mark.usefixtures('pypi_server')
def test_multiple_issues(tmpdir):
    # Make it a bit worse. The output should show all three issues.
    tmpdir.chdir()
    T.requirements('dependant_package\n-r %s/requirements.d/coverage.txt' % T.TOP)
    T.venv_update()

    T.run('./virtualenv_run/bin/pip', 'uninstall', '--yes', 'implicit_dependency')
    T.requirements('''
dependant_package
conflicting_package
pure_python_package==0.1.0
''')

    with pytest.raises(CalledProcessError) as excinfo:
        T.venv_update()
    assert excinfo.value.returncode == 1
    out, err = excinfo.value.result

    err = T.strip_coverage_warnings(err)
    assert err == ''

    out = T.uncolor(out)
    assert (
        '''
Cleaning up...
Error: unmet dependency: implicit-dependency (from dependant-package (from -r requirements.txt (line 2)))
Error: version conflict: many-versions-package 1 (virtualenv_run/%s)'''
        ''' <-> many-versions-package>=2,<4 (from dependant-package (from -r requirements.txt (line 2)))
Error: version conflict: pure-python-package 0.1.0 (virtualenv_run/%s)'''
        ''' <-> pure-python-package>=0.2.0 (from dependant-package (from -r requirements.txt (line 2)))
Storing debug log for failure in %s/home/.pip/pip.log

Something went wrong! Sending 'virtualenv_run' back in time, so make knows it's invalid.
''' % (PYTHON_LIB, PYTHON_LIB, tmpdir)
    ) in out

    assert_venv_marked_invalid(tmpdir.join('virtualenv_run'))


@pytest.mark.usefixtures('pypi_server')
def test_editable_egg_conflict(tmpdir):
    conflicting_package = tmpdir / 'tmp/conflicting_package'
    many_versions_package_2 = tmpdir / 'tmp/many_versions_package_2'

    from shutil import copytree
    copytree(
        str(T.TOP / 'tests/testing/packages/conflicting_package'),
        str(conflicting_package),
    )

    copytree(
        str(T.TOP / 'tests/testing/packages/many_versions_package_2'),
        str(many_versions_package_2),
    )

    with many_versions_package_2.as_cwd():
        from sys import executable as python
        T.run(python, 'setup.py', 'bdist_egg', '--dist-dir', str(conflicting_package))

    with tmpdir.as_cwd():
        T.requirements('-r %s/requirements.d/coverage.txt' % T.TOP)
        T.venv_update()

        T.requirements('-e %s' % conflicting_package)
        with pytest.raises(CalledProcessError) as excinfo:
            T.venv_update()
        assert excinfo.value.returncode == 1
        out, err = excinfo.value.result

        err = T.strip_coverage_warnings(err)
        assert err == ''

        out = T.uncolor(out)
        expected = '\nSuccessfully installed many-versions-package conflicting-package\n'
        assert expected in out
        rest = out.rsplit(expected, 1)[-1]

        if True:  # :pragma:nocover:pylint:disable=using-constant-test
            # Debian de-vendorizes the version of pip it ships
            try:
                from sysconfig import get_python_version
            except ImportError:  # <= python2.6
                from distutils.sysconfig import get_python_version
        assert (
            '''\
Cleaning up...
Error: version conflict: many-versions-package 2 (tmp/conflicting_package/many_versions_package-2-py{0}.egg)'''
            ''' <-> many-versions-package<2 (from conflicting-package==1 (from -r requirements.txt (line 1)))
Error: version conflict: many-versions-package 2 (tmp/conflicting_package/many_versions_package-2-py{0}.egg)'''
            ''' <-> many-versions-package<2 (from conflicting-package==1->-r requirements.txt (line 1))
Storing debug log for failure in {1}/home/.pip/pip.log

Something went wrong! Sending 'virtualenv_run' back in time, so make knows it's invalid.
Waiting for all subprocesses to finish...
DONE

'''.format(get_python_version(), tmpdir)
        ) == rest

        assert_venv_marked_invalid(tmpdir.join('virtualenv_run'))
