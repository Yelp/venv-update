#!/bin/bash
set -ex
TOP=${TOP:-.}
SITEPACKAGES=${SITEPACKAGES:-.}
PROJECT=venv_update

export PYTHONPATH=$(readlink -f $SITEPACKAGES)

python --version
coverage --version
py.test --version
coverage erase
coverage run --parallel-mode --rcfile=$TOP/.coveragerc \
    -m pytest "$@" $TOP/test $SITEPACKAGES/${PROJECT}.py
coverage combine
coverage report --fail-under 81  # FIXME: should be 100
mv .coverage $TOP
