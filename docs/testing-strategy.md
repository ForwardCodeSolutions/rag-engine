# Testing Strategy

## Structure
- tests/unit/ — isolated logic, mocked dependencies
- tests/integration/ — API endpoints, database, external services

## Rules
- Every new feature needs tests
- Use pytest fixtures, not setUp/tearDown
- Mock external services (LLM, databases) in unit tests
- Integration tests use Docker services

## Running
- All tests: `pytest tests/ -v`
- Unit only: `pytest tests/unit/ -v`
- With coverage: `pytest --cov=src tests/`
