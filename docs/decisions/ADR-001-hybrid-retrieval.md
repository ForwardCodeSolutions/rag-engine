# ADR-001: Hybrid Retrieval (Vector + BM25 + Knowledge Graph)

## Status
Accepted

## Context
Different types of queries require different retrieval approaches. Keyword-heavy queries (e.g., exact legal terms) perform better with lexical search, while semantic queries benefit from vector similarity. Entity-relationship queries are best served by graph traversal. A single retrieval method cannot optimally handle all query types.

## Decision
Use a hybrid retrieval approach combining three methods with weighted re-ranking:
1. **Vector search** (Qdrant) — semantic similarity via multilingual embeddings
2. **BM25** (rank-bm25) — keyword/lexical matching
3. **Knowledge Graph** (NetworkX) — entity and relationship-based retrieval

Results from all three methods are normalized and combined using configurable weights, then re-ranked to produce the final result set.

## Alternatives Considered
- **Vector search only** — rejected because it loses keyword precision for exact-match queries (legal terms, product codes, proper nouns)
- **BM25 only** — rejected because it lacks semantic understanding and cannot match paraphrased or multilingual queries
- **Vector + BM25 without graph** — rejected because entity-relationship queries (e.g., "documents mentioning company X and person Y") are poorly served by both methods

## Consequences
- Positive: best-of-all-worlds retrieval quality, handles diverse query types
- Positive: configurable weights allow tuning per use case
- Negative: increased complexity — three indexes to maintain per tenant
- Negative: slightly higher latency due to querying three sources and re-ranking
