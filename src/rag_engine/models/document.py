"""Document-related Pydantic models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    """Supported document types that determine chunking strategy."""

    LEGAL = "legal"
    TECHNICAL = "technical"
    GENERAL = "general"


class DocumentUpload(BaseModel):
    """Request model for document upload."""

    tenant_id: str = Field(description="Tenant identifier for data isolation")
    language: str | None = Field(
        default=None, description="Language hint (auto-detected if not provided)"
    )
    document_type: DocumentType = Field(
        default=DocumentType.GENERAL,
        description="Document type that affects chunking strategy",
    )


class DocumentMetadata(BaseModel):
    """Internal metadata stored alongside a document."""

    filename: str
    tenant_id: str
    language: str
    document_type: DocumentType
    chunk_count: int = 0
    file_size_bytes: int = 0


class DocumentResponse(BaseModel):
    """Response model returned after document upload or retrieval."""

    id: str = Field(description="Document identifier")
    filename: str = Field(description="Original filename")
    tenant_id: str = Field(description="Owning tenant")
    language: str = Field(description="Detected language")
    chunk_count: int = Field(description="Number of chunks created")
    created_at: datetime = Field(description="Upload timestamp")
