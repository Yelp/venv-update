from __future__ import absolute_import
from __future__ import unicode_literals

from subprocess import CalledProcessError

import pytest

from testing import requirements, run, uncolor, venv_update


def test_conflicting_reqs(tmpdir):
    tmpdir.chdir()
    requirements('''
# flake8 2.2.5 requires mccabe>=0.2.1, so this isn't satisfiable
flake8==2.2.5
mccabe==0.2
''')

    with pytest.raises(CalledProcessError) as excinfo:
        venv_update()

    assert excinfo.value.returncode == 1

    out, err = excinfo.value.result
    assert err == ''

    out = uncolor(out)
    assert '''
Successfully installed flake8 mccabe pyflakes pep8 setuptools
Cleaning up...
Error: version conflict: mccabe 0.2 <-> mccabe>=0.2.1 (from flake8==2.2.5 (from -r requirements.txt (line 3)))

Something went wrong! Sending 'virtualenv_run' back in time, so make knows it's invalid.
''' in out


def test_multiple_issues(tmpdir):
    # Make it a bit worse. The output should show all three issues.
    tmpdir.chdir()
    requirements('flake8==2.2.5')
    venv_update()

    run('./virtualenv_run/bin/pip', 'uninstall', '--yes', 'pyflakes')
    requirements('''
# flake8 2.2.5 requires mccabe>=0.2.1 and pep8>=1.5.7, so this isn't satisfiable
flake8==2.2.5
mccabe==0.2
pep8==1.0
''')

    with pytest.raises(CalledProcessError) as excinfo:
        venv_update()

    assert excinfo.value.returncode == 1

    out, err = excinfo.value.result
    assert err == ''

    out = uncolor(out)
    assert '''
Successfully installed mccabe pep8 setuptools
Cleaning up...
Error: unmet dependency: pyflakes>=0.8.1 (from flake8==2.2.5 (from -r requirements.txt (line 3)))
Error: version conflict: mccabe 0.2 <-> mccabe>=0.2.1 (from flake8==2.2.5 (from -r requirements.txt (line 3)))
Error: version conflict: pep8 1.0 <-> pep8>=1.5.7 (from flake8==2.2.5 (from -r requirements.txt (line 3)))

Something went wrong! Sending 'virtualenv_run' back in time, so make knows it's invalid.
''' in uncolor(out)
