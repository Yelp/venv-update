from __future__ import print_function
from __future__ import unicode_literals

import venv_update


def test_importable():
    assert venv_update


def test_parse_reqs(tmpdir):
    tmpdir.chdir()

    with open('setup.py', 'w') as setup:
        setup.write('\n')

    with open('reqs.txt', 'w') as reqs:
        reqs.write('''\
.

-r reqs2.txt
# a comment here
mccabe

pep8==1.0

-e hg+https://bitbucket.org/bukzor/coverage.py@__main__-support#egg=aweirdname
-e git+git://github.com/bukzor/cov-core.git@master#egg=cov-core
hg+https://bitbucket.org/logilab/pylint@58c66aa083777059a2e6b46f6a0545a2f4977097

file:///my/random/project
-e file:///my/random/project2
''')

    with open('reqs2.txt', 'w') as reqs:
        reqs.write('''\
pep8''')

    assert set(
        venv_update.pip_parse_requirements(('reqs.txt',))
    ) == set(
        ['mccabe', 'pep8', 'aweirdname', 'cov-core', None, 'pep8']
    )


def test_pip_get_installed():
    installed = venv_update.pip_get_installed()
    assert 'venv-update' in installed
