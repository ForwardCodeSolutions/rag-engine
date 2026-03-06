.PHONY: dev test test-fast test-property lint check fix coverage-html

dev:
	docker compose up -d

test:
	uv run pytest tests/ -v --cov=src/rag_engine --cov-report=term-missing --cov-report=html:htmlcov --cov-branch

test-fast:
	uv run pytest tests/ -x -q -n auto

test-property:
	uv run pytest tests/unit/test_property.py -v

lint:
	uv run ruff check src/ && uv run ruff format --check src/

fix:
	uv run ruff check src/ --fix && uv run ruff format src/

coverage-html: test
	open htmlcov/index.html

check: lint test
