# Data Models

## Request Models

### DocumentUpload (multipart form)
- `file`: UploadFile — the document file (PDF, DOCX, TXT, MD)
- `tenant_id`: str — tenant identifier for data isolation (1-128 alphanumeric/dash/underscore)
- `language`: str | None — language hint (auto-detected if not provided)
- `document_type`: str — "legal" | "technical" | "general" (affects chunking strategy)

### SearchQuery (JSON body)
- `query`: str — search text (max 2000 characters)
- `tenant_id`: str — tenant identifier (pattern: `^[a-zA-Z0-9_-]{1,128}$`)
- `top_k`: int — number of results to return (1-100, default: 10)
- `search_type`: SearchType — "hybrid" | "vector" | "bm25" | "graph" (default: "hybrid")
- `language`: str | None — language filter

### GDPR Delete (query parameters)
- `tenant_id`: str — tenant identifier (validated)
- `document_id`: str — document to delete (validated)
- `reason`: str — reason for deletion (audit log, default: "user request")

## Response Models

### DocumentResponse
- `id`: str — document identifier (UUID)
- `filename`: str — original filename
- `tenant_id`: str — owning tenant
- `language`: str — detected language
- `chunk_count`: int — number of chunks created
- `created_at`: datetime — upload timestamp

### SearchResult
- `document_id`: str — source document identifier
- `chunk_text`: str — matched text chunk
- `score`: float — combined relevance score
- `retrieval_method`: str — which method found this result
- `metadata`: dict — additional chunk metadata

### SearchResponse
- `query`: str — original search query
- `results`: list[SearchResult] — ranked results
- `total_results`: int — total number of results found

### DocumentDeleteResponse
- `document_id`: str — deleted document identifier
- `tenant_id`: str — owning tenant
- `bm25_chunks_removed`: int — chunks removed from BM25 index
- `graph_chunks_removed`: int — chunks removed from knowledge graph
- `message`: str — confirmation message

### GDPRDeleteResponse
- `tenant_id`: str — tenant whose data was deleted
- `documents_removed`: int — total items removed across all backends
- `message`: str — confirmation message

### HealthResponse
- `status`: str — "healthy" | "degraded" | "unhealthy"
- `qdrant_connected`: bool — Qdrant connection status
- `version`: str — API version
