from py._path.local import LocalPath as Path

TOP = Path(__file__) / '../..'
SCENARIOS = TOP/'tests/scenarios'


def get_scenario(name):
    """Sync all the files from test/scenarios/{name} to the current directory
    """
    # Trailing slash is essential to rsync
    run('rsync', '-a', '%s/%s/' % (SCENARIOS, name), '.')


def run(*cmd, **env):
    from subprocess import check_call

    if env:
        from os import environ
        tmp = env
        env = environ.copy()
        env.update(tmp)
    else:
        env = None

    check_call(cmd, env=env)


def venv_update(*args):
    # we get coverage for free via the (patched) pytest-cov plugin
    run(
        'venv-update',
        *args,
        HOME=str(Path('.').realpath())
    )


def venv_update_symlink_pwd():
    # I wish I didn't need this =/
    # surely there's a better way -.-
    # NOTE: `pip install TOP` causes an infinite copyfiles loop, under tox >.<
    from venv_update import __file__ as venv_update_path, dotpy

    # symlink so that we get coverage, where possible
    venv_update_path = Path(dotpy(venv_update_path))
    local_vu = Path(venv_update_path.basename)
    if local_vu.exists():
        local_vu.remove()
    local_vu.mksymlinkto(venv_update_path)


def venv_update_script(pyscript, venv='virtualenv_run'):
    """Run a python script that imports venv_update"""

    # symlink so that we get coverage, where possible
    venv_update_symlink_pwd()

    # write it to a file so we get more-reasonable stack traces
    testscript = Path('testscript.py')
    testscript.write(pyscript)
    run('%s/bin/python' % venv, testscript.strpath)


# coverage.py adds some helpful warnings to stderr, with no way to quiet them.
from re import compile as Regex, MULTILINE
coverage_warnings_regex = Regex(
    r'^Coverage.py warning: (Module .* was never imported\.|No data was collected\.)\n',
    flags=MULTILINE,
)


def strip_coverage_warnings(stderr):
    return coverage_warnings_regex.sub('', stderr)
