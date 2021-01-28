venv-update
===========
Quickly and exactly synchronize a large python project's virtualenv with its
[requirements](https://pip.pypa.io/en/stable/user_guide/#requirements-files).

[![PyPI version](https://badge.fury.io/py/venv-update.svg)](https://pypi.python.org/pypi/venv-update)
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


Yelpers
=======
To develop and run tests suites on a devbox, make sure to:

1. Python 3.6.0 on a xenial devbox breaks coverage. Use a bionic devbox instead.

2. Override pip.conf to use public pypi. Don't forget to delete it after you're done!
```
$ cat ~/.pip/pip.conf
[global]
index-url = https://pypi.org/simple/
```

3. `sudo apt-get install pypy-dev` so TOXENV=pypy doesn't fail spectacularly
