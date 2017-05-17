venv-update
===========
Quickly and exactly synchronize a large python project's virtualenv with its
[requirements](https://pip.pypa.io/en/stable/user_guide/#requirements-files).

[![PyPI version](https://badge.fury.io/py/venv-update.svg)](https://pypi.python.org/pypi/venv-update)
[![Travis CI](https://img.shields.io/travis/Yelp/venv-update/master.svg?label=travis-ci)](https://travis-ci.org/Yelp/venv-update/branches)
[![Coverage](https://codecov.io/github/Yelp/venv-update/coverage.svg?branch=master)](https://codecov.io/github/Yelp/venv-update?branch=master)
[![Documentation](https://readthedocs.org/projects/venv-update/badge/?version=master)](http://venv-update.readthedocs.org/en/master/)


Please see http://venv-update.readthedocs.org/en/master/ for the complete documentation.


How to Contribute
-----------------

1. Fork this repository on github: https://help.github.com/articles/fork-a-repo/
2. Clone it: https://help.github.com/articles/cloning-a-repository/
3. Make a feature branch for your changes:

        git remote add upstream https://github.com/Yelp/venv-update.git
        git fetch upstream
        git checkout upstream/master -b my-feature-branch

4. Make sure the test suite works before you start:

        source .activate.sh
        make test

5. Commit patches: http://gitref.org/basic/
6. Push to github: `git pull && git push origin`
7. Send a pull request: https://help.github.com/articles/creating-a-pull-request/


### Running tests: ###

Run a particular test:

    py.test tests/functional/simple_test.py::test_downgrade


See all output from a test:

    py.test -s -k downgrade


Check coverage of a single test:

    ./test tests/functional/simple_test.py::test_downgrade
