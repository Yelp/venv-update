from py._path.local import LocalPath as Path


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


# coverage.py adds some helpful warnings to stderr, with no way to quiet them.
from re import compile as Regex, MULTILINE
coverage_warnings_regex = Regex(
    r'^Coverage.py warning: (Module .* was never imported\.|No data was collected\.)\n',
    flags=MULTILINE,
)


def strip_coverage_warnings(stderr):
    return coverage_warnings_regex.sub('', stderr)
