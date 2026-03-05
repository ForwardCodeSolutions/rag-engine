.PHONY: dev test lint check fix

dev:
	docker compose up -d

test:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	uv run ruff check src/ && uv run ruff format --check src/

fix:
	uv run ruff check src/ --fix && uv run ruff format src/

check: lint test
