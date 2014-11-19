from py._path.local import LocalPath as Path

from testing import get_scenario, run, venv_update


def test_is_relocatable(tmpdir):
    tmpdir.chdir()
    get_scenario('trivial')
    venv_update()

    Path('virtualenv_run').rename('relocated')

    pip = 'relocated/bin/pip'
    assert Path(pip).exists()
    run(pip, '--version')
