.PHONY: dev test lint check fix

dev:
	docker compose up -d

test:
	pytest tests/ -v

lint:
	ruff check src/ && ruff format --check src/

fix:
	ruff check src/ --fix && ruff format src/

check: lint test
