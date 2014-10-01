#!/bin/bash
set -ex
TOP=${TOP:-.}

flake8 --version
flake8 $TOP

pylint --version
# This is equivalent to the flake8 $TOP behavior:
pylint --rcfile=$TOP/pylintrc $(
    find $TOP -name .tox -prune -or -name '*.py' -print |
    egrep -v '(.*\.tmp|tmp/|\.tox)'  # same as flake8 settings
)

## blocked on pylint bug: https://bitbucket.org/logilab/pylint/pull-request/186
# pylint $TOP/$PROJECT $TOP/*.py $TOP/tests/*
## blocked on pylint bug: https://bitbucket.org/logilab/pylint/issue/352
# pylint .

(cd $TOP && pre-commit run --all-files)
