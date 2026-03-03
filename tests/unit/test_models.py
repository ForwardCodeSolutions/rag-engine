"""Tests for Pydantic models."""

from datetime import datetime

from rag_engine.models.document import (
    DocumentMetadata,
    DocumentResponse,
    DocumentType,
    DocumentUpload,
)
from rag_engine.models.health import HealthResponse, HealthStatus
from rag_engine.models.search import SearchQuery, SearchResponse, SearchResult, SearchType


class TestDocumentModels:
    """Tests for document-related models."""

    def test_document_upload_defaults(self) -> None:
        upload = DocumentUpload(tenant_id="tenant-1")
        assert upload.tenant_id == "tenant-1"
        assert upload.language is None
        assert upload.document_type == DocumentType.GENERAL

    def test_document_upload_with_all_fields(self) -> None:
        upload = DocumentUpload(
            tenant_id="tenant-1",
            language="en",
            document_type=DocumentType.LEGAL,
        )
        assert upload.language == "en"
        assert upload.document_type == DocumentType.LEGAL

    def test_document_metadata(self) -> None:
        metadata = DocumentMetadata(
            filename="contract.pdf",
            tenant_id="tenant-1",
            language="it",
            document_type=DocumentType.LEGAL,
            chunk_count=15,
            file_size_bytes=204800,
        )
        assert metadata.filename == "contract.pdf"
        assert metadata.chunk_count == 15

    def test_document_response(self) -> None:
        now = datetime.now()
        response = DocumentResponse(
            id="doc-123",
            filename="report.pdf",
            tenant_id="tenant-1",
            language="en",
            chunk_count=10,
            created_at=now,
        )
        assert response.id == "doc-123"
        assert response.created_at == now


class TestSearchModels:
    """Tests for search-related models."""

    def test_search_query_defaults(self) -> None:
        query = SearchQuery(query="test query", tenant_id="tenant-1")
        assert query.top_k == 10
        assert query.search_type == SearchType.HYBRID
        assert query.language is None

    def test_search_query_custom(self) -> None:
        query = SearchQuery(
            query="contratto",
            tenant_id="tenant-1",
            top_k=5,
            search_type=SearchType.BM25,
            language="it",
        )
        assert query.top_k == 5
        assert query.search_type == SearchType.BM25

    def test_search_result(self) -> None:
        result = SearchResult(
            document_id="doc-1",
            chunk_text="Some matched text",
            score=0.95,
            retrieval_method="vector",
        )
        assert result.score == 0.95
        assert result.metadata == {}

    def test_search_response(self) -> None:
        result = SearchResult(
            document_id="doc-1",
            chunk_text="chunk",
            score=0.9,
            retrieval_method="hybrid",
        )
        response = SearchResponse(
            query="test",
            results=[result],
            total_results=1,
        )
        assert len(response.results) == 1
        assert response.total_results == 1


class TestHealthModel:
    """Tests for health check model."""

    def test_health_response_healthy(self) -> None:
        health = HealthResponse(
            status=HealthStatus.HEALTHY,
            qdrant_connected=True,
            version="0.1.0",
        )
        assert health.status == HealthStatus.HEALTHY
        assert health.qdrant_connected is True

    def test_health_response_degraded(self) -> None:
        health = HealthResponse(
            status=HealthStatus.DEGRADED,
            qdrant_connected=False,
            version="0.1.0",
        )
        assert health.status == HealthStatus.DEGRADED
        assert health.qdrant_connected is False
