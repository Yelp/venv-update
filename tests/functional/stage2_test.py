"""
We need to test "stage 2" independently for coverage measurements.
The coverage tool loses track of it because it's run via os.exec().
"""
from __future__ import print_function
from __future__ import unicode_literals
import pytest

from testing import get_scenario, run, strip_coverage_warnings, TOP
import venv_update


def stage2(executable, tmpdir):
    run(
        executable,
        venv_update.__file__,
        '--stage2',
        'myvenv',
        HOME=tmpdir.strpath,
    )


def test_trivial(tmpdir):
    tmpdir.chdir()
    get_scenario('trivial')

    with open('requirements.txt', 'w') as requirements:
        # An arbitrary small package: mccabe
        requirements.write('mccabe\npep8==1.0')

    run('virtualenv', 'myvenv')
    # need this to get coverage. surely there's a better way...
    run(
        'myvenv/bin/pip',
        'install',
        '-r', (TOP/'requirements.d/coverage.txt').strpath
    )

    stage2('myvenv/bin/python', tmpdir)


def test_error_with_wrong_python(tmpdir, capfd):
    from sys import executable

    tmpdir.chdir()
    get_scenario('trivial')

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        stage2(executable, tmpdir)

    assert excinfo.value.returncode == 1
    out, err = capfd.readouterr()
    lasterr = strip_coverage_warnings(err).rsplit('\n', 2)[-2]

    assert lasterr == 'AssertionError: Executable not in venv: %s != %s/myvenv/bin/python' % (executable, tmpdir.strpath)
    assert out == ''


def test_touch_on_error(tmpdir, capfd):
    from sys import executable

    tmpdir.chdir()
    get_scenario('trivial')

    from os import mkdir
    mkdir('myvenv')

    from subprocess import CalledProcessError
    with pytest.raises(CalledProcessError) as excinfo:
        stage2(executable, tmpdir)

    assert excinfo.value.returncode == 1
    out, err = capfd.readouterr()
    lasterr = strip_coverage_warnings(err).rsplit('\n', 2)[-2]

    assert lasterr == 'AssertionError: Executable not in venv: %s != %s/myvenv/bin/python' % (executable, tmpdir.strpath)
    assert out.startswith('> touch myvenv ')
