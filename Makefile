PYTHON?=python2.7
REQUIREMENTS?=requirements.txt

.PHONY: all
all: lint test

.PHONY: lint
lint: venv
	./venv/bin/pre-commit run --all-files

.PHONY: test tests
test tests: venv
	. venv/bin/activate && ./test $(ARGS)

venv: setup.py requirements.txt requirements.d/* Makefile
	./venv_update.py venv= --python=$(PYTHON) venv install= -r $(REQUIREMENTS)
	./venv/bin/pre-commit install

.PHONY: clean
clean:
	rm -rf .tox
	find -name '*.pyc' -print0 | xargs -0 -r -P4 rm
