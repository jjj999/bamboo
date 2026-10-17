.PHONY: install lint format format-check typecheck test-unit \
	test-integration test-slow test-all build check

POETRY_RUN := poetry run
PYTEST := $(POETRY_RUN) pytest -o addopts= --strict-markers

install:
	poetry config virtualenvs.in-project true --local
	poetry install --with dev,docs

lint:
	$(POETRY_RUN) ruff check .

format:
	$(POETRY_RUN) ruff format .

format-check:
	$(POETRY_RUN) ruff format --check .

typecheck:
	$(POETRY_RUN) pyright

test-unit:
	$(PYTEST) -m "not integration and not slow"

test-integration:
	$(PYTEST) -m "integration and not slow"

test-slow:
	$(PYTEST) -m "slow"

test-all:
	$(PYTEST) -m "not slow"

build:
	$(POETRY_RUN) python -m build

check: lint typecheck test-all
