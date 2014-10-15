from py._path.local import LocalPath as Path

TOP = Path(__file__) / '../../..'
SCENARIOS = TOP/'testing/data/scenarios'


def run(*cmd, **env):
    from pipes import quote
    from subprocess import check_call

    if env:
        from os import environ
        tmp = env
        env = environ.copy()
        env.update(tmp)
    else:
        env = None

    check_call(('echo', '\033[01;36m>\033[m \033[01;33m{0}\033[m'.format(
        ' '.join(quote(arg) for arg in cmd)
    )))
    check_call(cmd, env=env)


def test_trivial(tmpdir):
    pwd = Path('.').realpath()
    tmpdir.chdir()

    # Trailing slash is essential to rsync
    run('rsync', '-a', str(SCENARIOS) + '/trivial/', '.')
    run(
        'coverage',
        'run',
        '--parallel-mode',
        '--rcfile', str(TOP/'.coveragerc'),
        '-m', 'venv_update',
        COVERAGE_FILE=str(TOP/'.coverage'),
    )

    pwd.chdir()
