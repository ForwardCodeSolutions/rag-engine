---
name: build-test-verify
description: Run build, tests, and verification after code changes. Use after implementing any feature, fixing bugs, or refactoring code.
---
After making code changes:

1. Run linter: `make lint`
   - If errors found, fix them before proceeding
2. Run tests: `make test`
   - If tests fail, fix the code, not the tests
3. If both pass, the change is ready for commit

If any step fails:
- Read the error message carefully
- Fix the root cause (not symptoms)
- Run the full check again: `make check`

Never skip verification. Never commit failing code.
