# Architecture

## System Overview

```mermaid
graph TB
    Client[Client / API Consumer]
    API[FastAPI REST API]
    Ingest[Document Ingestion Pipeline]
    Chunk[Smart Chunker]
    Embed[Multilingual Embedder]
    Qdrant[(Qdrant Vector DB)]
    BM25[(BM25 Index)]
    KG[(Knowledge Graph)]
    Hybrid[Hybrid Retriever]
    Rerank[Re-Ranker]
    GDPR[GDPR Compliance Layer]

    Client --> API
    API --> Ingest
    Ingest --> Chunk
    Chunk --> Embed
    Embed --> Qdrant
    Chunk --> BM25
    Chunk --> KG
    API --> Hybrid
    Hybrid --> Qdrant
    Hybrid --> BM25
    Hybrid --> KG
    Hybrid --> Rerank
    Rerank --> API
    GDPR --> Qdrant
    GDPR --> BM25
    GDPR --> KG
```

## Components

- **FastAPI REST API** — Entry point for all client interactions
- **Document Ingestion Pipeline** — Parses, chunks, and embeds uploaded documents
- **Smart Chunker** — Adaptive chunking strategies (legal, technical, general)
- **Multilingual Embedder** — sentence-transformers with multilingual model
- **Qdrant Vector DB** — Vector similarity search with tenant isolation
- **BM25 Index** — Keyword-based retrieval per language
- **Knowledge Graph** — NetworkX-based entity/relation graph
- **Hybrid Retriever** — Combines results from all three retrieval methods
- **Re-Ranker** — Weighted score normalization and re-ranking
- **GDPR Compliance Layer** — Tenant isolation, right to erasure, audit logging
