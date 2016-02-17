.PHONY: all
all: lint test

.PHONY: lint
lint: venv
	tox -e lint

.PHONY: test tests
test tests: venv
	. venv/bin/activate && ./test $(ARGS)

.PHONY: tox
tox:
	tox -e lint,py27

venv: setup.py requirements.txt requirements.d/* Makefile
	./venv_update.py venv= --python=python2.7 venv
	./venv/bin/pre-commit install

.PHONY: clean
clean:
	rm -rf .tox
	find -name '*.pyc' -print0 | xargs -0 -r -P4 rm
