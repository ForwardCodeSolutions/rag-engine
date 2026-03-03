"""GDPR-related Pydantic models."""

from pydantic import BaseModel, Field


class GDPRDeleteRequest(BaseModel):
    """Request model for tenant data deletion."""

    tenant_id: str = Field(description="Tenant whose data should be deleted")
    reason: str = Field(description="Reason for deletion (audit log)")


class GDPRDeleteResponse(BaseModel):
    """Response model confirming data deletion."""

    tenant_id: str = Field(description="Tenant whose data was deleted")
    documents_removed: int = Field(description="Number of documents removed")
    message: str = Field(description="Confirmation message")


class DocumentDeleteResponse(BaseModel):
    """Response model confirming document deletion."""

    document_id: str = Field(description="Deleted document identifier")
    tenant_id: str = Field(description="Owning tenant")
    bm25_chunks_removed: int = Field(description="BM25 chunks removed")
    graph_chunks_removed: int = Field(description="Knowledge graph chunks removed")
    message: str = Field(description="Confirmation message")
