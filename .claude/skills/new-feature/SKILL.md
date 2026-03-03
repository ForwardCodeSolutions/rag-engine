---
name: new-feature
description: Implement a new feature following the project workflow. Use when adding new functionality, endpoints, or components.
---
## Workflow: Research → Plan → Implement → Test → Review

### 1. Plan
- Create ADR in `docs/decisions/` if this involves an architectural choice
- Read `docs/code-conventions.md` for naming and style rules
- Read `docs/architecture.md` to understand where this fits

### 2. Implement (in this order)
- Define Pydantic models in `src/rag_engine/models/`
- Write service logic in `src/rag_engine/services/`
- Create API route in `src/rag_engine/api/`
- Add error handling with specific exceptions

### 3. Test
- Write unit tests in `tests/unit/`
- Write integration tests if API endpoint involved
- Run `make check` — must pass

### 4. Document
- Update `docs/api.md` if new endpoint added
- Update README.md if user-facing change

### 5. Commit
- Use the git-commit skill for proper commit format
