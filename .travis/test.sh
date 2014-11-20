#!/bin/bash
set -ex
export TOP=$(readlink -f ${TOP:-.})
export SITEPACKAGES=${SITEPACKAGES:-.}
export PROJECT=venv_update
NCPU=$(getconf _NPROCESSORS_CONF)

coverage erase
py.test -n $NCPU \
    --cov --cov-config=$TOP/.coveragerc --cov-report='' \
    "$@" $TOP/tests $SITEPACKAGES/${PROJECT}.py
coverage combine
coverage report --rcfile=$TOP/.coveragerc --fail-under 97  # FIXME: should be 100
