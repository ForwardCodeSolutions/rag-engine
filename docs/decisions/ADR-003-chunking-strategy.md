# ADR-003: Adaptive Chunking Strategy

## Status
Accepted

## Context
Documents uploaded to the system vary significantly in structure and purpose: legal contracts have articles and clauses, technical documentation has sections and code blocks, general text has paragraphs and headings. A one-size-fits-all chunking approach produces suboptimal results — either too coarse (losing precision) or too fine (losing context).

## Decision
Implement adaptive chunking with three strategies, selected based on document type:
1. **Legal** — chunk by articles, clauses, and numbered sections, preserving legal structure
2. **Technical** — chunk by sections, headings, and code blocks, keeping related content together
3. **General/Semantic** — chunk by semantic similarity, splitting when topic shifts significantly

The document type is specified at upload time or auto-detected. Each strategy maintains configurable overlap between chunks to preserve context at boundaries.

## Alternatives Considered
- **Fixed-size chunking** (e.g., 512 tokens) — rejected because it breaks mid-sentence and mid-concept, destroying context for legal and technical documents
- **Sentence-level chunking** — rejected because individual sentences lack sufficient context for meaningful retrieval
- **Single semantic chunking for all types** — rejected because legal structure (articles, clauses) is critical for legal documents and semantic splitting doesn't preserve it

## Consequences
- Positive: significantly better retrieval quality for specialized document types
- Positive: preserves document structure meaningful to end users
- Negative: more complex ingestion pipeline with multiple code paths
- Negative: requires document type classification (manual or automatic)
