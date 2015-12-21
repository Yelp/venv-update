.PHONY: all
all: lint test

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: test tests
test tests: venv
	. venv-venv_update/bin/activate && ./test $(ARGS)

.PHONY: tox
tox:
	tox -e lint,test

.PHONY: venv
venv: venv-venv_update
venv-venv_update: setup.py requirements.d/* Makefile
	rm -rf venv-venv_update
	virtualenv --python=python2.7 venv-venv_update
	rm -rf venv-venv_update/local
	# TODO use pip-faster
	venv-venv_update/bin/pip install -r requirements.d/dev.txt
	venv-venv_update/bin/pre-commit install

.PHONY: clean
clean:
	rm -rf .tox
	find -name '*.pyc' -print0 | xargs -0 -r -P4 rm
