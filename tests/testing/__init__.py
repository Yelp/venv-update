# NOTE WELL: No side-effects are allowed in __init__ files. This means you!
from py._path.local import LocalPath as Path
from re import compile as Regex, MULTILINE

TOP = Path(__file__) / '../../..'


def requirements(reqs):
    """Write a requirements.txt file to the current working directory."""
    Path('requirements.txt').write(reqs)


def run(*cmd, **env):
    if env:
        from os import environ
        tmp = env
        env = environ.copy()
        env.update(tmp)
    else:
        env = None

    from .capture_subprocess import capture_subprocess
    from venv_update import colorize
    capture_subprocess(('echo', '\nTEST>', colorize(cmd)))
    out, err = capture_subprocess(cmd, env=env)
    err = strip_coverage_warnings(err)
    return out, err


def venv_update(*args, **env):
    # we get coverage for free via the (patched) pytest-cov plugin
    return run(
        'venv-update',
        *args,
        HOME=str(Path('.').realpath()),
        **env
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
    return run('%s/bin/python' % venv, testscript.strpath)


# coverage.py adds some helpful warnings to stderr, with no way to quiet them.
coverage_warnings_regex = Regex(
    r'^Coverage.py warning: (Module .* was never imported\.|No data was collected\.)\n',
    flags=MULTILINE,
)


def strip_coverage_warnings(stderr):
    return coverage_warnings_regex.sub('', stderr)


def uncolor(text):
    # the colored_tty, uncolored_pipe tests cover this pretty well.
    from re import sub
    return sub('\033\\[[^A-z]*[A-z]', '', text)
