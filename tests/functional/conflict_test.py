from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
from subprocess import CalledProcessError
from sysconfig import get_python_version

import pytest

import testing as T
from testing.python_lib import PYTHON_LIB


def assert_venv_marked_invalid(venv):
    """we mark a virtualenv as invalid by bumping its timestamp back by a day"""
    venv_age = time.time() - os.path.getmtime(venv.strpath)
    assert venv_age / 60 / 60 / 24 > 1


def assert_something_went_wrong(out):
    assert out.endswith(
        'Something went wrong! '
        "Sending 'venv' back in time, so make knows it's invalid.\n"
    )


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
    err = T.strip_pip_warnings(err)
    assert err == (
        "conflicting-package 1 has requirement many-versions-package<2, but you'll "
        'have many-versions-package 3 which is incompatible.\n'
        # TODO: do we still need to append our own error?
        'Error: version conflict: many-versions-package 3 (venv/{}) '
        '<-> many-versions-package<2 '
        '(from conflicting_package->-r requirements.txt (line 3))\n'.format(
            PYTHON_LIB,
        )
    )

    out = T.uncolor(out)
    assert_something_went_wrong(out)

    assert_venv_marked_invalid(tmpdir.join('venv'))


@pytest.mark.usefixtures('pypi_server')
def test_multiple_issues(tmpdir):
    # Make it a bit worse. The output should show all three issues.
    tmpdir.chdir()
    T.enable_coverage()

    T.requirements('dependant_package\n-r %s/requirements.d/coverage.txt' % T.TOP)
    T.venv_update()

    T.run('./venv/bin/pip', 'uninstall', '--yes', 'implicit_dependency')
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
    err = T.strip_pip_warnings(err)

    err = err.splitlines()
    # pip outputs conflict lines in a non-consistent order
    assert set(err[:3]) == {
        'dependant-package 1 requires implicit-dependency, which is not installed.',
        "dependant-package 1 has requirement pure-python-package>=0.2.1, but you'll have pure-python-package 0.1.0 which is incompatible.",  # noqa
        "conflicting-package 1 has requirement many-versions-package<2, but you'll have many-versions-package 3 which is incompatible.",  # noqa
    }
    # TODO: do we still need to append our own error?
    assert '\n'.join(err[3:]) == (
        'Error: version conflict: pure-python-package 0.1.0 '
        '(venv/{lib}) <-> pure-python-package>=0.2.1 '
        '(from dependant_package->-r requirements.txt (line 2))\n'
        'Error: version conflict: many-versions-package 3 '
        '(venv/{lib}) <-> many-versions-package<2 '
        '(from conflicting_package->-r requirements.txt (line 3))'.format(
            lib=PYTHON_LIB,
        )
    )

    out = T.uncolor(out)
    assert_something_went_wrong(out)

    assert_venv_marked_invalid(tmpdir.join('venv'))


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
        T.enable_coverage()
        T.requirements('-e %s' % conflicting_package)
        with pytest.raises(CalledProcessError) as excinfo:
            T.venv_update()
        assert excinfo.value.returncode == 1
        out, err = excinfo.value.result

        err = T.strip_coverage_warnings(err)
        err = T.strip_pip_warnings(err)
        assert err == (
            'Error: version conflict: many-versions-package 2 '
            '(tmp/conflicting_package/many_versions_package-2-py{}.egg) '
            '<-> many_versions_package<2 '
            '(from conflicting-package==1->-r requirements.txt (line 1))\n'.format(
                get_python_version(),
            )
        )

        out = T.uncolor(out)
        assert_something_went_wrong(out)

        assert_venv_marked_invalid(tmpdir.join('venv'))
