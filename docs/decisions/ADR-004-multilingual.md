# ADR-004: Multilingual Support Approach

## Status
Accepted

## Context
The system must support documents and queries in Italian, English, and Russian from day one. This affects embedding model selection, BM25 indexing, and search quality across languages.

## Decision
- **Embedding model**: Use `intfloat/multilingual-e5-large` (or `paraphrase-multilingual-MiniLM-L12-v2` as lighter alternative) — a single model that handles all supported languages in one vector space
- **Language detection**: Use `langdetect` library at document upload time to identify language
- **BM25 indexes**: Maintain separate BM25 indexes per language, since BM25 tokenization and stemming are language-specific
- **Cross-lingual search**: Vector search handles cross-lingual queries natively (same embedding space); BM25 is language-filtered

## Alternatives Considered
- **Separate embedding models per language** — rejected because it requires multiple vector spaces, complicates cross-lingual search, and increases resource usage
- **Translation-based approach** (translate everything to English) — rejected because translation introduces errors, adds latency, and loses language-specific nuances
- **English-only with optional translation** — rejected because it doesn't meet the core requirement of native multilingual support

## Consequences
- Positive: single embedding space enables cross-lingual semantic search
- Positive: language detection is automatic, minimal user friction
- Positive: BM25 per language ensures accurate keyword matching
- Negative: multilingual models may have slightly lower quality per-language compared to monolingual models
- Negative: BM25 index maintenance scales with number of languages
