# Code Conventions

## Naming
- Readable English names: `user_documents` not `ud`
- Boolean: `is_active`, `has_permission`, `can_edit`
- Constants: UPPER_SNAKE_CASE in config.py

## Functions
- Single responsibility: one function = one thing
- Max 30 lines per function
- All public functions have docstrings
- Type hints everywhere (Python 3.11+ style)

## Error Handling
- Specific exceptions, never bare `except:`
- Custom exceptions in src/rag_engine/exceptions.py

## Logging
- structlog for structured logs, never print()
- Log levels: debug/info/warning/error

## Data Validation
- Pydantic v2 for all request/response models
- Settings via pydantic-settings + .env

## Dependencies
- uv for package management (not pip)
- pyproject.toml (not setup.py)
- ruff for linting + formatting
