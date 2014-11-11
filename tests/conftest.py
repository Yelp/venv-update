import pytest


@pytest.fixture(scope="session", autouse=True)
def no_pip_environment_vars():
    import os
    for var in os.environ.keys():
        if var.startswith('PIP_'):
            del os.environ[var]
