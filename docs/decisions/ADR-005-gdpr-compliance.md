# ADR-005: GDPR Compliance by Design

## Status
Accepted

## Context
The system processes documents for EU clients, making GDPR compliance mandatory. Key requirements: data isolation between tenants, right to erasure (Article 17), and auditability of data operations.

## Decision
Implement GDPR compliance as a core architectural concern, not an afterthought:
1. **Tenant isolation**: Each tenant gets a separate Qdrant collection, separate BM25 index, and separate knowledge graph subgraph. No data mixing between tenants.
2. **Right to erasure**: Dedicated API endpoints (`DELETE /api/v1/documents/{id}` and `DELETE /api/v1/tenants/{id}/data`) that cascade deletion across all storage backends (Qdrant, BM25, Knowledge Graph).
3. **Audit logging**: All data operations (upload, search, delete) are logged with structured logs (structlog) including tenant_id, operation type, timestamp, and affected resources.

## Alternatives Considered
- **Shared collections with metadata filtering** — rejected because a bug in filtering could leak data between tenants; true isolation is safer
- **GDPR as optional middleware** — rejected because retrofitting data isolation is extremely difficult; must be built-in from the start
- **External audit system** — rejected for initial version; structured logging is sufficient, can integrate external audit later

## Consequences
- Positive: strong data isolation prevents cross-tenant data leaks
- Positive: complete data erasure is guaranteed by design
- Positive: audit trail for compliance reporting
- Negative: more collections/indexes to manage (one set per tenant)
- Negative: cannot do cross-tenant analytics or search without explicit data sharing agreement
