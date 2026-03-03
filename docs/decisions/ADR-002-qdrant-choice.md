# ADR-002: Qdrant as Vector Database

## Status
Accepted

## Context
The system needs a vector database for storing and searching document embeddings. The database must support tenant isolation (separate collections), self-hosting for GDPR compliance, and efficient similarity search at scale.

## Decision
Use Qdrant as the vector database. Key reasons:
- **Open-source and self-hosted** — critical for GDPR compliance, data stays on our infrastructure
- **Rust-based** — high performance with low resource consumption
- **REST + gRPC API** — easy integration with Python via qdrant-client
- **Collection-based isolation** — natural tenant separation
- **Filtering** — metadata filtering during search (language, document type)
- **Docker-ready** — simple deployment with Docker Compose

## Alternatives Considered
- **Pinecone** — rejected because it's cloud-only SaaS, data leaves our infrastructure (GDPR concern), vendor lock-in
- **Weaviate** — viable option but heavier resource footprint, Go-based (less efficient for our scale), more complex configuration
- **Milvus** — rejected because it requires multiple dependencies (etcd, MinIO), over-engineered for our use case
- **ChromaDB** — rejected because it lacks production-readiness, limited filtering, no built-in replication

## Consequences
- Positive: full data control, GDPR-compliant by design
- Positive: lightweight Docker deployment, minimal operational overhead
- Positive: active community and frequent releases
- Negative: self-hosted means we manage infrastructure and backups
- Negative: smaller ecosystem compared to Pinecone
