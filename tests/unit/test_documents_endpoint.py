"""Tests for document upload and search endpoints."""

from fastapi.testclient import TestClient

from rag_engine.api.app import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-api-key"}


class TestUploadEndpoint:
    """Tests for POST /api/v1/documents/upload."""

    def test_upload_txt_file(self) -> None:
        response = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": "tenant-1"},
            files={"file": ("doc.txt", b"Hello world from test document", "text/plain")},
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "doc.txt"
        assert data["tenant_id"] == "tenant-1"
        assert data["chunk_count"] >= 1
        assert "id" in data
        assert "language" in data

    def test_upload_md_file(self) -> None:
        response = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": "tenant-1"},
            files={"file": ("readme.md", b"# Title\n\nSome content here", "text/plain")},
            headers=HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["chunk_count"] >= 1

    def test_upload_unsupported_format(self) -> None:
        response = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": "tenant-1"},
            files={"file": ("data.csv", b"a,b,c", "text/csv")},
            headers=HEADERS,
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_upload_empty_file(self) -> None:
        response = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": "tenant-1"},
            files={"file": ("empty.txt", b"", "text/plain")},
            headers=HEADERS,
        )
        assert response.status_code == 400

    def test_upload_with_language_hint(self) -> None:
        response = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": "tenant-1", "language": "it"},
            files={"file": ("doc.txt", b"Ciao mondo questo e un test", "text/plain")},
            headers=HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["language"] == "it"

    def test_upload_with_document_type(self) -> None:
        response = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": "tenant-1", "document_type": "legal"},
            files={"file": ("contract.txt", b"Article 1. Terms apply.", "text/plain")},
            headers=HEADERS,
        )
        assert response.status_code == 200

    def test_upload_invalid_document_type(self) -> None:
        response = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": "tenant-1", "document_type": "invalid"},
            files={"file": ("doc.txt", b"content", "text/plain")},
            headers=HEADERS,
        )
        assert response.status_code == 400


class TestSearchEndpoint:
    """Tests for POST /api/v1/documents/search."""

    def test_search_empty_index(self) -> None:
        response = client.post(
            "/api/v1/documents/search",
            json={"query": "test", "tenant_id": "empty-tenant"},
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 0
        assert data["results"] == []

    def test_search_returns_response_shape(self) -> None:
        response = client.post(
            "/api/v1/documents/search",
            json={"query": "hello", "tenant_id": "tenant-1"},
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total_results" in data

    def test_search_with_search_type(self) -> None:
        response = client.post(
            "/api/v1/documents/search",
            json={
                "query": "test",
                "tenant_id": "tenant-1",
                "search_type": "bm25",
            },
            headers=HEADERS,
        )
        assert response.status_code == 200

    def test_search_with_language_filter(self) -> None:
        response = client.post(
            "/api/v1/documents/search",
            json={
                "query": "test",
                "tenant_id": "tenant-1",
                "language": "en",
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
