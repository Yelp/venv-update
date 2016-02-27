venv-update
===========
Quickly and exactly synchronize a large python project's virtualenv with its
[requirements](https://pip.pypa.io/en/stable/user_guide/#requirements-files).

[![PyPI version](https://badge.fury.io/py/venv-update.svg)]
(https://pypi.python.org/pypi/venv-update)
[![Build Status (circle)](https://circleci.com/gh/Yelp/pip-faster)]
(https://circleci.com/gh/Yelp/venv-update.svg?style=shield)
[![Build Status (travis)](https://travis-ci.org/Yelp/venv-update.svg?branch=stable)]
(https://travis-ci.org/Yelp/venv-update)
[![Coverage Status](https://codecov.io/github/Yelp/venv-update/coverage.svg?branch=stable)]
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
