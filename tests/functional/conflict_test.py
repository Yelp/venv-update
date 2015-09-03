from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from subprocess import CalledProcessError

import pytest
import testing as T


def test_conflicting_reqs(tmpdir):
    tmpdir.chdir()
    T.requirements('''
# flake8 2.2.5 requires mccabe>=0.2.1, so this isn't satisfiable
flake8==2.2.5
mccabe==0.2
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
Error: version conflict: mccabe 0.2 (virtualenv_run/lib/python2.7/site-packages)'''
        ''' <-> mccabe>=0.2.1 (from flake8==2.2.5 (from -r requirements.txt (line 3)))

Something went wrong! Sending 'virtualenv_run' back in time, so make knows it's invalid.
'''
    ) in out


def test_multiple_issues(tmpdir):
    # Make it a bit worse. The output should show all three issues.
    tmpdir.chdir()
    T.requirements('flake8==2.2.5')
    T.venv_update()

    T.run('./virtualenv_run/bin/pip', 'uninstall', '--yes', 'pyflakes')
    T.requirements('''
# flake8 2.2.5 requires mccabe>=0.2.1 and pep8>=1.5.7, so this isn't satisfiable
flake8==2.2.5
mccabe==0.2
pep8==1.0
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
Error: version conflict: mccabe 0.2 (virtualenv_run/lib/python2.7/site-packages)'''
        ''' <-> mccabe>=0.2.1 (from flake8==2.2.5 (from -r requirements.txt (line 3)))
Error: version conflict: pep8 1.0 (virtualenv_run/lib/python2.7/site-packages) '''
        '''<-> pep8>=1.5.7 (from flake8==2.2.5 (from -r requirements.txt (line 3)))
Error: unmet dependency: pyflakes>=0.8.1 (from flake8==2.2.5 (from -r requirements.txt (line 3)))

Something went wrong! Sending 'virtualenv_run' back in time, so make knows it's invalid.
'''
    ) in out
