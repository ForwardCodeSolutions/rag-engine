---
name: create-adr
description: Create an Architecture Decision Record. Use when making a significant technical choice like selecting a database, framework, or approach.
---
Create ADR in `docs/decisions/` with this format:

## Template: docs/decisions/ADR-NNN-title.md

```
# ADR-NNN: [Decision Title]

## Status
Accepted

## Context
[Why did this question come up? What problem are we solving?]

## Decision
[What we chose and why]

## Alternatives Considered
- **Alternative A**: [description] — rejected because [reason]
- **Alternative B**: [description] — rejected because [reason]

## Consequences
- Positive: [benefits]
- Negative: [tradeoffs we accept]
```

## Rules
- Number sequentially: ADR-001, ADR-002, etc.
- One decision per ADR
- Write BEFORE implementing (not after)
- Keep under 1 page
