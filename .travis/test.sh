#!/bin/bash
set -ex
TOP=$(readlink -f ${TOP:-.})
SITEPACKAGES=${SITEPACKAGES:-.}
PROJECT=venv_update
NCPU=$(getconf _NPROCESSORS_CONF)

python --version
coverage --version
py.test --version
coverage erase
py.test -n $NCPU \
    --cov-enable --cov-config=$TOP/.coveragerc --cov-report='' \
    "$@" $TOP/tests $SITEPACKAGES/${PROJECT}.py
coverage combine
coverage report --rcfile=$TOP/.coveragerc --fail-under 95  # FIXME: should be 100
