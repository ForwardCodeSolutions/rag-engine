# Data Models

## Request Models

### DocumentUpload
- `file`: UploadFile — the document file (PDF, DOCX, TXT, MD)
- `tenant_id`: str — tenant identifier for data isolation
- `language`: str | None — language hint (auto-detected if not provided)
- `document_type`: str — "legal" | "technical" | "general" (affects chunking strategy)

### SearchQuery
- `query`: str — search text
- `tenant_id`: str — tenant identifier
- `top_k`: int — number of results to return (default: 10)
- `search_type`: str — "hybrid" | "vector" | "bm25" | "graph" (default: "hybrid")
- `language`: str | None — language filter

### GDPRDeleteRequest
- `tenant_id`: str — tenant whose data should be deleted
- `reason`: str — reason for deletion (audit log)

## Response Models

### DocumentResponse
- `id`: str — document identifier
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

### TenantConfig
- `tenant_id`: str — tenant identifier
- `collection_name`: str — Qdrant collection name
- `created_at`: datetime — tenant creation timestamp

### HealthResponse
- `status`: str — "healthy" | "degraded" | "unhealthy"
- `qdrant_connected`: bool — Qdrant connection status
- `version`: str — API version
