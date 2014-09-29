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

.PHONY: clean
clean:
	find -name '*.pyc' -print0 | xargs -0 rm
	rm -rf .tox
