export PYTHON?=python2.7
export REQUIREMENTS?=requirements.txt

.PHONY: all
all: lint test

.PHONY: lint
lint: venv
	. venv/bin/activate && pre-commit run --all-files

.PHONY: test tests
test tests: venv
	. venv/bin/activate && ./test $(ARGS)

venv: setup.py requirements.txt requirements.d/* Makefile
	./venv_update.py venv= --python=$(PYTHON) venv install= -r $(REQUIREMENTS)

.PHONY: docs
docs: venv
	make -C docs serve

.PHONY: clean
clean:
	rm -rf .tox
	find -name '*.pyc' -print0 | xargs -0 -r -P4 rm

.PHONY: clean
release: venv
	./bin/release
