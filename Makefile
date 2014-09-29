.PHONY: all
all: lint test

.PHONY: lint test
lint : ./.travis/lint.sh
test : ./.travis/test.sh
lint test:
	$<

.PHONY: tox
tox:
	tox -e lint,test
