from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import time
from subprocess import CalledProcessError

import pytest
import testing as T
from testing.python_lib import PYTHON_LIB


def assert_venv_age(tmpdir):
    venv_dir = tmpdir.join('virtualenv_run')
    venv_age = time.time() - os.path.getmtime(venv_dir.strpath)
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
Storing debug log for failure in %s/.pip/pip.log

Something went wrong! Sending 'virtualenv_run' back in time, so make knows it's invalid.
''' % (PYTHON_LIB, tmpdir)
    ) in out

    assert_venv_age(tmpdir)


@pytest.mark.usefixtures('pypi_server')
def test_multiple_issues(tmpdir):
    # Make it a bit worse. The output should show all three issues.
    tmpdir.chdir()
    T.requirements('dependant_package')
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
Storing debug log for failure in %s/.pip/pip.log

Something went wrong! Sending 'virtualenv_run' back in time, so make knows it's invalid.
''' % (PYTHON_LIB, PYTHON_LIB, tmpdir)
    ) in out

    assert_venv_age(tmpdir)
