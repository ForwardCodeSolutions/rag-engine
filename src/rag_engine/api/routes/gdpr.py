"""GDPR compliance API endpoints."""

from fastapi import APIRouter, Depends, Query, Request

from rag_engine.api.dependencies import get_gdpr_service, validate_id, verify_api_key
from rag_engine.api.routes.rate_limit import limiter
from rag_engine.models.gdpr import (
    DocumentDeleteResponse,
    GDPRDeleteResponse,
)
from rag_engine.services.gdpr import GDPRService

router = APIRouter(tags=["gdpr"], dependencies=[Depends(verify_api_key)])

_gdpr_service_dep = Depends(get_gdpr_service)


@router.delete("/documents/{document_id}", response_model=DocumentDeleteResponse)
@limiter.limit("10/minute")
async def delete_document(
    request: Request,
    document_id: str,
    tenant_id: str = Query(description="Tenant owning the document"),
    reason: str = Query(default="user request", description="Reason for deletion"),
    gdpr_service: GDPRService = _gdpr_service_dep,  # noqa: B008
) -> DocumentDeleteResponse:
    """Delete a document and all its indexed data (GDPR).

    Cascades deletion across BM25 index, Knowledge Graph, and Qdrant.
    """
    validate_id(tenant_id, "tenant_id")
    validate_id(document_id, "document_id")
    result = gdpr_service.delete_document(
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
@limiter.limit("10/minute")
async def delete_tenant_data(
    request: Request,
    tenant_id: str,
    reason: str = Query(
        default="GDPR right to erasure",
        description="Reason for deletion (audit log)",
    ),
    gdpr_service: GDPRService = _gdpr_service_dep,  # noqa: B008
) -> GDPRDeleteResponse:
    """Delete all data belonging to a tenant (GDPR right to erasure).

    Permanently removes all documents, indexes, and graph data
    for the specified tenant.
    """
    result = gdpr_service.delete_tenant_data(
        tenant_id=tenant_id,
        reason=reason,
    )

    return GDPRDeleteResponse(
        tenant_id=tenant_id,
        documents_removed=result["total_removed"],
        message=f"All data for tenant {tenant_id} deleted successfully",
    )
