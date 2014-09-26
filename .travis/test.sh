#!/bin/bash
set -ex
shopt -s globstar

python --version
coverage --version
coverage erase
coverage run -m pytest "$@" tests
coverage report --show-missing --fail-under 100
flake8 --version
flake8 $(git ls-files '*.py')
pylint --version
pylint $(git ls-files '*.py')
