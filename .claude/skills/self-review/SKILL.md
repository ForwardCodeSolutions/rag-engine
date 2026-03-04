---
name: self-review
description: Review code before committing. Use as final check before any git commit.
---
Review checklist — verify ALL items:

## Naming & Style
- [ ] Variable names are readable English (not abbreviations)
- [ ] Functions are under 30 lines
- [ ] Type hints on all function signatures (including return types)
- [ ] Docstrings on classes, `__init__`, and all public functions

## Logic
- [ ] No hardcoded values — use config.py or .env
- [ ] Specific exception handling (no bare except:)
- [ ] Edge cases handled (empty input, None, invalid data)
- [ ] No code duplication — extract shared patterns into helpers

## Security
- [ ] No secrets in code (use .env)
- [ ] All destructive endpoints require authentication (X-API-Key)
- [ ] User input validated: tenant_id, document_id, query (length, format)
- [ ] File paths validated against base directory (no path traversal)
- [ ] CORS configured with explicit allow_origins (not wildcard)

## GDPR
- [ ] User data is tenant-isolated in ALL backends (BM25, KG, Qdrant)
- [ ] Delete endpoints cascade to ALL stores including Qdrant vectors
- [ ] Audit log captures operation, tenant, resource, reason, timestamp
- [ ] Delete responses return real counts (not hardcoded 0)

## Architecture
- [ ] API routes don't import directly from storage/ — use services layer
- [ ] No module-level singletons for stores — use Depends() DI
- [ ] Deterministic IDs (hashlib, not hash()) for Qdrant points

## Tests
- [ ] New code has corresponding tests
- [ ] Tests include error paths (401, 400, 422), not just happy path
- [ ] API tests include X-API-Key header
- [ ] `make check` passes

If any item fails — fix it before committing.
