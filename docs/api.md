# API Specification

Base URL: `http://localhost:8000/api/v1`

## Endpoints

### System

#### `GET /health`

Health check endpoint. Returns service status and version.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "qdrant_connected": false,
  "version": "0.1.0"
}
```

### GDPR — Document Deletion

#### `DELETE /documents/{document_id}`

Delete a document and all its indexed data across BM25, Knowledge Graph, and Qdrant.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | string | yes | Tenant owning the document |
| `reason` | string | no | Reason for deletion (default: "user request") |

**Response** `200 OK`:
```json
{
  "document_id": "doc-123",
  "tenant_id": "tenant-1",
  "bm25_chunks_removed": 3,
  "graph_chunks_removed": 3,
  "message": "Document doc-123 deleted successfully"
}
```

### GDPR — Tenant Data Erasure

#### `DELETE /tenants/{tenant_id}/data`

Delete ALL data belonging to a tenant (GDPR Article 17 — Right to Erasure). Cascades across all storage backends.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `reason` | string | no | Reason for deletion (default: "GDPR right to erasure") |

**Response** `200 OK`:
```json
{
  "tenant_id": "tenant-1",
  "documents_removed": 0,
  "message": "All data for tenant tenant-1 deleted successfully"
}
```

## Models

See [models.md](models.md) for all Pydantic request/response models.

## Authentication

API key authentication via `API_KEY` environment variable (not yet enforced).

## OpenAPI

Interactive documentation available at `http://localhost:8000/docs` when the server is running.
