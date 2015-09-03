.PHONY: all
all: lint test

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: test tests
test tests:
	./test $(ARGS)

.PHONY: tox
tox:
	tox -e lint,test

.PHONY: venv
venv:
	tox -ve venv
	# see: https://bitbucket.org/ned/coveragepy/issue/340/keyerror-subpy#comment-13671053
	rm -rf venv-venv_update/local/

.PHONY: clean
clean:
	rm -rf .tox
	find -name '*.pyc' -print0 | xargs -0 -r -P4 rm
