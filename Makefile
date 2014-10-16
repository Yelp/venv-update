.PHONY: all
all: lint test

.PHONY: lint
lint:
	pre-commit run --all

.PHONY: test
test:
	./.travis/test.sh $(ARGS)

.PHONY: tox
tox:
	tox -e lint,test

.PHONY: clean
clean:
	find -name '*.pyc' -print0 | xargs -0 rm
	rm -rf .tox
