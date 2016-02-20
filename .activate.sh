export TOP=$PWD
make venv
. venv/bin/activate
pre-commit install
