PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
TEST ?= pytest

.PHONY: install test clean

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e .[dev]

test:
	$(TEST) -q

clean:
	rm -rf build dist *.egg-info .pytest_cache
