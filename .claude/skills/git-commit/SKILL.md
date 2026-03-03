---
name: git-commit
description: Create a well-formatted git commit. Use after build-test-verify passes successfully.
---
## Commit format
Use conventional commits: `type: short description`

Types: feat, fix, docs, refactor, test, chore

## Rules
- One logical change per commit
- Message in English, lowercase, no period at end
- Max 72 characters for subject line
- If change is complex, add body after blank line

## Examples
- `feat: add hybrid search combining vector and BM25 retrieval`
- `fix: handle empty document in chunking pipeline`
- `refactor: extract embedding logic into separate service`
- `test: add integration tests for search API`
- `docs: add ADR for Qdrant selection`

## Process
1. Run `make check` first (never commit failing code)
2. Stage relevant files: `git add <specific files>`
3. Commit with meaningful message
4. Never use `git add .` blindly
