venv-update
===========
Quickly and exactly synchronize a large python project's virtualenv with its
[requirements](https://pip.pypa.io/en/stable/user_guide/#requirements-files).

[![PyPI version](https://badge.fury.io/py/venv-update.svg)]
(https://pypi.python.org/pypi/venv-update)
[![Circle CI](https://circleci.com/gh/Yelp/venv-update/tree/stable.svg?style=shield)]
(https://circleci.com/gh/Yelp/venv-update/tree/stable)
[![Travis CI](https://img.shields.io/travis/Yelp/venv-update/stable.svg?label=travis-ci)]
(https://travis-ci.org/Yelp/venv-update/branches)
[![Coverage](https://codecov.io/github/Yelp/venv-update/coverage.svg?branch=stable)]
(https://codecov.io/github/Yelp/venv-update?branch=stable)
[![Documentation](https://readthedocs.org/projects/venv-update/badge/)]
(http://venv-update.readthedocs.org/en/stable/)


Please see http://venv-update.readthedocs.org/en/stable/ for the complete documentation.


Development
-----------

Fork this repository on github. (see https://help.github.com/articles/fork-a-repo/)
Clone it. (https://help.github.com/articles/cloning-a-repository/)
Run these commands:

    source .activate.sh
    make test

Once you see the tests pass, feel free to commit patches.
You'll need to make the tests pass again before any pull request is accepted.


### Running tests: ###

getting full output from a test:

    py.test -k thattest -vs -n0


Run a particular test:

    py.test tests/functional/simple_test.py::test_downgrade


Check coverage of a test:

    ./test tests/functional/simple_test.py::test_downgrade
