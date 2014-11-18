import pytest


@pytest.fixture(scope="session", autouse=True)
def no_pip_environment_vars():
    import os
    for var in dict(os.environ):
        if var.startswith('PIP_'):
            del os.environ[var]


@pytest.fixture(scope="session", autouse=True)
def no_pythonpath_environment_var():
    import os
    for var in dict(os.environ):
        if var == 'PYTHONPATH':
            del os.environ[var]


@pytest.fixture(scope="session")
def sdist(request):
    import sys
    from testing import run, TOP

    # I don't believe there's a better way :pylint:disable=protected-access
    tmpdir = request.config._tmpdirhandler.mktemp('sdist')

    TOP.chdir()
    run(
        sys.executable,
        TOP.join('setup.py').strpath,
        '--quiet',
        'sdist',
        '--dist-dir', tmpdir.strpath,
    )

    dists = tuple(tmpdir.visit('*.tar.gz'))
    assert len(dists) == 1, dists

    return dists[0]
