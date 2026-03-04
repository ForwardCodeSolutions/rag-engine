"""Tests for GDPR compliance service and API endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from rag_engine.services.gdpr import GDPRService
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore
from rag_engine.utils.audit import log_operation


class TestGDPRServiceDeleteDocument:
    """Tests for document deletion."""

    def _setup(self) -> tuple[GDPRService, BM25Store, KnowledgeGraphStore]:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        service = GDPRService(bm25, graph)
        return service, bm25, graph

    def test_delete_document_from_bm25(self) -> None:
        service, bm25, _graph = self._setup()
        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "some text")])

        result = service.delete_document("tenant-1", "doc-1")
        assert result["bm25_chunks_removed"] == 1
        assert bm25.search("tenant-1", "some", "en") == []

    def test_delete_document_from_graph(self) -> None:
        service, _bm25, graph = self._setup()
        graph.add_documents("tenant-1", [("doc-1", 0, "Alice works here.")])

        result = service.delete_document("tenant-1", "doc-1")
        assert result["graph_chunks_removed"] == 1
        assert graph.search("tenant-1", "Alice") == []

    def test_delete_document_from_both(self) -> None:
        service, bm25, graph = self._setup()
        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "Alice works here")])
        graph.add_documents("tenant-1", [("doc-1", 0, "Alice works here.")])

        result = service.delete_document("tenant-1", "doc-1")
        assert result["bm25_chunks_removed"] == 1
        assert result["graph_chunks_removed"] == 1

    def test_delete_nonexistent_document(self) -> None:
        service, _bm25, _graph = self._setup()
        result = service.delete_document("tenant-1", "no-such-doc")
        assert result["bm25_chunks_removed"] == 0
        assert result["graph_chunks_removed"] == 0

    def test_delete_preserves_other_documents(self) -> None:
        service, bm25, _graph = self._setup()
        bm25.add_documents(
            "tenant-1",
            "en",
            [
                ("doc-1", 0, "first document text"),
                ("doc-2", 0, "second document text"),
            ],
        )

        service.delete_document("tenant-1", "doc-1")
        results = bm25.search("tenant-1", "second", "en")
        assert len(results) == 1


class TestGDPRServiceDeleteTenant:
    """Tests for tenant data deletion (right to erasure)."""

    def test_delete_tenant_clears_bm25(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        service = GDPRService(bm25, graph)

        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "text")])
        bm25.add_documents("tenant-1", "it", [("doc-2", 0, "testo")])

        service.delete_tenant_data("tenant-1")
        assert bm25.search("tenant-1", "text", "en") == []
        assert bm25.search("tenant-1", "testo", "it") == []

    def test_delete_tenant_clears_graph(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        service = GDPRService(bm25, graph)

        graph.add_documents("tenant-1", [("doc-1", 0, "Alice works here.")])

        service.delete_tenant_data("tenant-1")
        assert graph.search("tenant-1", "Alice") == []

    def test_delete_tenant_preserves_other_tenants(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        service = GDPRService(bm25, graph)

        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "tenant one data")])
        bm25.add_documents("tenant-2", "en", [("doc-2", 0, "tenant two data")])

        service.delete_tenant_data("tenant-1")
        assert bm25.search("tenant-1", "tenant", "en") == []
        assert len(bm25.search("tenant-2", "tenant", "en")) == 1


class TestAuditLogging:
    """Tests for audit log function."""

    def test_log_operation_does_not_raise(self) -> None:
        # Should not raise regardless of arguments
        log_operation(
            operation="delete",
            tenant_id="tenant-1",
            resource_type="document",
            resource_id="doc-1",
            reason="test",
        )

    @patch("rag_engine.utils.audit.audit_logger")
    def test_log_operation_calls_logger(self, mock_logger) -> None:
        log_operation(
            operation="delete",
            tenant_id="tenant-1",
            resource_type="document",
            resource_id="doc-1",
            reason="user request",
        )
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args
        assert call_kwargs[1]["operation"] == "delete"
        assert call_kwargs[1]["tenant_id"] == "tenant-1"

    @patch("rag_engine.services.gdpr.log_operation")
    def test_delete_document_triggers_audit(self, mock_audit) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        service = GDPRService(bm25, graph)

        service.delete_document("tenant-1", "doc-1", reason="GDPR request")
        mock_audit.assert_called_once()
        assert mock_audit.call_args[1]["operation"] == "delete"
        assert mock_audit.call_args[1]["reason"] == "GDPR request"

    @patch("rag_engine.services.gdpr.log_operation")
    def test_delete_tenant_triggers_audit(self, mock_audit) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        service = GDPRService(bm25, graph)

        service.delete_tenant_data("tenant-1", reason="account closure")
        mock_audit.assert_called_once()
        assert mock_audit.call_args[1]["operation"] == "delete_all"
        assert mock_audit.call_args[1]["reason"] == "account closure"


class TestGDPREndpoints:
    """Tests for GDPR API endpoints."""

    _headers = {"X-API-Key": "test-api-key"}

    def _get_client(self) -> TestClient:
        from rag_engine.api.app import app

        return TestClient(app)

    def test_delete_document_endpoint(self) -> None:
        client = self._get_client()
        response = client.delete(
            "/api/v1/documents/doc-123",
            params={"tenant_id": "tenant-1", "reason": "test deletion"},
            headers=self._headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-123"
        assert data["tenant_id"] == "tenant-1"
        assert "deleted successfully" in data["message"]

    def test_delete_tenant_data_endpoint(self) -> None:
        client = self._get_client()
        response = client.delete(
            "/api/v1/tenants/tenant-1/data",
            params={"reason": "GDPR erasure request"},
            headers=self._headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "tenant-1"
        assert "deleted successfully" in data["message"]

    def test_delete_document_without_auth_returns_401(self) -> None:
        client = self._get_client()
        response = client.delete(
            "/api/v1/documents/doc-123",
            params={"tenant_id": "tenant-1"},
        )
        assert response.status_code == 422  # missing required header

    def test_delete_document_with_wrong_key_returns_401(self) -> None:
        client = self._get_client()
        response = client.delete(
            "/api/v1/documents/doc-123",
            params={"tenant_id": "tenant-1"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401
