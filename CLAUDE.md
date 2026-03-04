# rag-engine

## Why
Lightweight RAG engine for multilingual document search with hybrid retrieval (Vector + BM25 + Knowledge Graph). Built for EU clients with GDPR compliance.

## What
- `src/rag_engine/api/` — FastAPI routes (upload, search, delete)
- `src/rag_engine/core/` — Hybrid retrieval, reranker
- `src/rag_engine/ingestion/` — Document parsing, chunking, embedding
- `src/rag_engine/models/` — Pydantic models
- `src/rag_engine/storage/` — Qdrant, BM25, Knowledge Graph adapters
- `tests/` — pytest (unit + integration)

## How

### Commands
- Run: `make dev` → http://localhost:8000/docs
- Test: `make check` (ruff + pytest)
- Dependencies: `uv sync`

### Verify changes
After ANY change, run `make check`. Do not commit if it fails.

### Further reading
**IMPORTANT:** Read relevant docs before making changes.
- `docs/architecture.md` — System diagram and component overview
- `docs/api.md` — All endpoints with request/response examples
- `docs/decisions/` — ADRs (Qdrant choice, chunking strategy, etc.)
- `docs/code-conventions.md` — Naming, style, patterns
- `docs/testing-strategy.md` — What to test and how
- `docs/audit-fixes.md` — Post-audit fix checklist (track progress here)
- `docs/audit-technical-spec.md` — Technical spec for each fix

## Critical rules
- Hybrid search: vector + BM25 + knowledge graph with weighted re-ranking
- Multilingual: Italian, English, Russian (multilingual embeddings)
- GDPR: tenant isolation, right to erasure, audit logging
- All secrets via .env (QDRANT_URL, EMBEDDING_MODEL, API_KEY)
