#!/bin/bash
set -ex
TOP=${TOP:-.}
SITEPACKAGES=${SITEPACKAGES:-.}
PROJECT=venv_update

python --version
coverage --version
py.test --version
coverage erase
coverage run --rcfile=$TOP/.coveragerc \
    -m pytest "$@" $TOP/tests $SITEPACKAGES/$PROJECT
coverage report --show-missing --fail-under 25  # FIXME: should be 100
