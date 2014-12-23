.PHONY: all
all: lint test

.PHONY: lint
lint:
	pre-commit run --all

.PHONY: test tests
test tests:
	./.travis/test.sh $(ARGS)

.PHONY: tox
tox:
	tox -e lint,test

.PHONY: clean
clean:
	rm -rf .tox
	find -name '*.pyc' -print0 | xargs -0 -r -P4 rm
