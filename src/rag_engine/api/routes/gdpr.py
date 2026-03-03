"""GDPR compliance API endpoints."""

from fastapi import APIRouter, Query

from rag_engine.models.gdpr import (
    DocumentDeleteResponse,
    GDPRDeleteResponse,
)
from rag_engine.services.gdpr import GDPRService
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore

router = APIRouter(tags=["gdpr"])

# Shared store instances (will be replaced with dependency injection later)
_bm25_store = BM25Store()
_graph_store = KnowledgeGraphStore()
_gdpr_service = GDPRService(_bm25_store, _graph_store)


@router.delete("/documents/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    tenant_id: str = Query(description="Tenant owning the document"),
    reason: str = Query(default="user request", description="Reason for deletion"),
) -> DocumentDeleteResponse:
    """Delete a document and all its indexed data (GDPR).

    Cascades deletion across BM25 index and Knowledge Graph.
    """
    result = _gdpr_service.delete_document(
        tenant_id=tenant_id,
        document_id=document_id,
        reason=reason,
    )

    return DocumentDeleteResponse(
        document_id=document_id,
        tenant_id=tenant_id,
        bm25_chunks_removed=result["bm25_chunks_removed"],
        graph_chunks_removed=result["graph_chunks_removed"],
        message=f"Document {document_id} deleted successfully",
    )


@router.delete("/tenants/{tenant_id}/data", response_model=GDPRDeleteResponse)
async def delete_tenant_data(
    tenant_id: str,
    reason: str = Query(
        default="GDPR right to erasure",
        description="Reason for deletion (audit log)",
    ),
) -> GDPRDeleteResponse:
    """Delete all data belonging to a tenant (GDPR right to erasure).

    Permanently removes all documents, indexes, and graph data
    for the specified tenant.
    """
    _gdpr_service.delete_tenant_data(
        tenant_id=tenant_id,
        reason=reason,
    )

    return GDPRDeleteResponse(
        tenant_id=tenant_id,
        documents_removed=0,
        message=f"All data for tenant {tenant_id} deleted successfully",
    )
