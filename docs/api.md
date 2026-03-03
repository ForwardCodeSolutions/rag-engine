# API Specification

## Endpoints

### Document Management

#### `POST /api/v1/documents/upload`
Upload a document for processing and indexing.

#### `POST /api/v1/documents/search`
Search across indexed documents using hybrid retrieval.

#### `GET /api/v1/documents/{id}`
Get information about a specific document.

#### `DELETE /api/v1/documents/{id}`
Delete a document and all its indexed data (GDPR).

### GDPR

#### `DELETE /api/v1/tenants/{id}/data`
Delete all data belonging to a tenant (GDPR right to erasure).

### System

#### `GET /api/v1/health`
Health check endpoint.

#### `GET /api/v1/metrics`
Quality metrics and system statistics.
