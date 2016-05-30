SRC_PATH = .

UNIT_TEST_PATH = tests
UNIT_TEST_PATTERN = *_test.py
INT_TEST_PATH = tests
INT_TEST_PATTERN = *_int.py
TEST_CMD = make test
DOCS_PATH = docs

ifndef VERBOSE
	MAKEFLAGS += --no-print-directory
endif

test:
	python -m unittest discover -s $(UNIT_TEST_PATH) -p $(UNIT_TEST_PATTERN)

int-test:
	python -m unittest discover -s $(INT_TEST_PATH) -p $(INT_TEST_PATTERN)

watch:
	watchmedo shell-command --patterns='*.py' --ignore-directories --recursive --command="$(TEST_CMD)" -W .

watch-docs:
	watchmedo shell-command --patterns='*.rst;*.py' --ignore-directories --recursive --command="$(DOCS_CMD)" -W .

.PHONY: docs
docs:
	$(MAKE) -C $(DOCS_PATH) html

upload-test:
	python setup.py bdist_wheel upload -r https://testpypi.python.org/pypi

upload:
	python setup.py bdist_wheel upload


