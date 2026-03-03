---
name: self-review
description: Review code before committing. Use as final check before any git commit.
---
Review checklist — verify ALL items:

## Naming & Style
- [ ] Variable names are readable English (not abbreviations)
- [ ] Functions are under 30 lines
- [ ] Type hints on all function signatures
- [ ] Docstrings on classes and public functions

## Logic
- [ ] No hardcoded values — use config.py or .env
- [ ] Specific exception handling (no bare except:)
- [ ] Edge cases handled (empty input, None, invalid data)

## Security & GDPR
- [ ] No secrets in code (use .env)
- [ ] User data is tenant-isolated
- [ ] Delete endpoints cascade properly

## Tests
- [ ] New code has corresponding tests
- [ ] `make check` passes

If any item fails — fix it before committing.
