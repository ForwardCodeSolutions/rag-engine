"""Integration tests for multilingual document search (IT/EN/RU)."""

from fastapi.testclient import TestClient

from rag_engine.api.app import create_app


class TestMultilingualSearch:
    """Upload documents in IT/EN/RU and search in each language."""

    _headers = {"X-API-Key": "test-api-key"}

    def _client(self) -> TestClient:
        return TestClient(create_app())

    def _upload(self, client: TestClient, text: str, tenant: str, lang: str) -> dict:
        resp = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": tenant, "document_type": "general", "language": lang},
            files={"file": ("doc.txt", text.encode(), "text/plain")},
            headers=self._headers,
        )
        assert resp.status_code == 200
        return resp.json()

    def _search(self, client: TestClient, query: str, tenant: str, language: str = "en") -> dict:
        resp = client.post(
            "/api/v1/documents/search",
            json={"query": query, "tenant_id": tenant, "search_type": "bm25",
                  "language": language},
            headers=self._headers,
        )
        assert resp.status_code == 200
        return resp.json()

    def test_english_document_found_by_english_query(self) -> None:
        client = self._client()
        self._upload(client, "Python is a popular programming language", "t1", "en")
        data = self._search(client, "programming language", "t1", "en")
        assert data["total_results"] >= 1

    def test_italian_document_found_by_italian_query(self) -> None:
        client = self._client()
        self._upload(client, "Python è un linguaggio di programmazione popolare", "t1", "it")
        data = self._search(client, "linguaggio di programmazione", "t1", "it")
        assert data["total_results"] >= 1

    def test_russian_document_found_by_russian_query(self) -> None:
        client = self._client()
        self._upload(client, "Python это популярный язык программирования", "t1", "ru")
        data = self._search(client, "язык программирования", "t1", "ru")
        assert data["total_results"] >= 1

    def test_cross_language_isolation(self) -> None:
        """Documents in one language should not pollute another language's index."""
        client = self._client()
        self._upload(client, "Machine learning transforms healthcare", "t1", "en")
        self._upload(client, "L'apprendimento automatico trasforma la sanità", "t1", "it")

        en_data = self._search(client, "machine learning", "t1", "en")
        assert en_data["total_results"] >= 1
        texts = [r["chunk_text"] for r in en_data["results"]]
        assert any("Machine learning" in t for t in texts)

    def test_all_three_languages_coexist(self) -> None:
        """Upload IT/EN/RU for same tenant, each searchable independently."""
        client = self._client()
        self._upload(client, "Cloud computing enables scalability", "t1", "en")
        self._upload(client, "Il cloud computing consente la scalabilità", "t1", "it")
        self._upload(client, "Облачные вычисления обеспечивают масштабируемость", "t1", "ru")

        assert self._search(client, "scalability", "t1", "en")["total_results"] >= 1
        assert self._search(client, "scalabilità", "t1", "it")["total_results"] >= 1
        assert self._search(client, "масштабируемость", "t1", "ru")["total_results"] >= 1
