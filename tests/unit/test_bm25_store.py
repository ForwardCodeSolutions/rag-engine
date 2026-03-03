"""Tests for BM25 keyword search store."""

from rag_engine.storage.bm25_store import BM25Store, tokenize


class TestTokenize:
    """Tests for the tokenize helper."""

    def test_basic_tokenization(self) -> None:
        assert tokenize("Hello World") == ["hello", "world"]

    def test_empty_string(self) -> None:
        assert tokenize("") == []


class TestBM25StoreAddAndSearch:
    """Tests for adding documents and searching."""

    def test_add_and_search_single_document(self) -> None:
        store = BM25Store()
        store.add_documents("tenant-1", "en", [("doc-1", 0, "machine learning algorithms")])

        results = store.search("tenant-1", "machine learning", "en")
        assert len(results) == 1
        assert results[0][0] == "doc-1"
        assert results[0][3] > 0

    def test_search_returns_ranked_results(self) -> None:
        store = BM25Store()
        store.add_documents(
            "tenant-1",
            "en",
            [
                ("doc-1", 0, "introduction to python programming"),
                ("doc-2", 0, "python python python advanced patterns"),
                ("doc-3", 0, "java enterprise architecture"),
            ],
        )

        results = store.search("tenant-1", "python", "en")
        assert len(results) >= 2
        assert results[0][0] == "doc-2"  # more "python" mentions = higher score

    def test_search_respects_top_k(self) -> None:
        store = BM25Store()
        store.add_documents(
            "tenant-1",
            "en",
            [
                ("doc-1", 0, "first document about search"),
                ("doc-2", 0, "second document about search"),
                ("doc-3", 0, "third document about search"),
            ],
        )

        results = store.search("tenant-1", "search", "en", top_k=2)
        assert len(results) <= 2

    def test_search_empty_index_returns_empty(self) -> None:
        store = BM25Store()
        results = store.search("tenant-1", "query", "en")
        assert results == []

    def test_search_empty_query_returns_empty(self) -> None:
        store = BM25Store()
        store.add_documents("tenant-1", "en", [("doc-1", 0, "some text")])
        results = store.search("tenant-1", "", "en")
        assert results == []

    def test_search_no_match_returns_empty(self) -> None:
        store = BM25Store()
        store.add_documents("tenant-1", "en", [("doc-1", 0, "machine learning")])
        results = store.search("tenant-1", "gastronomy", "en")
        assert results == []

    def test_add_returns_chunk_count(self) -> None:
        store = BM25Store()
        count = store.add_documents(
            "tenant-1",
            "en",
            [
                ("doc-1", 0, "first chunk"),
                ("doc-1", 1, "second chunk"),
            ],
        )
        assert count == 2


class TestBM25StoreTenantIsolation:
    """Tests for per-tenant data isolation."""

    def test_tenants_are_isolated(self) -> None:
        store = BM25Store()
        store.add_documents("tenant-1", "en", [("doc-1", 0, "secret data")])
        store.add_documents("tenant-2", "en", [("doc-2", 0, "other data")])

        results_t1 = store.search("tenant-1", "secret", "en")
        results_t2 = store.search("tenant-2", "secret", "en")

        assert len(results_t1) == 1
        assert results_t2 == []


class TestBM25StoreLanguageIsolation:
    """Tests for per-language index isolation."""

    def test_languages_are_isolated(self) -> None:
        store = BM25Store()
        store.add_documents("tenant-1", "en", [("doc-1", 0, "english document")])
        store.add_documents("tenant-1", "it", [("doc-2", 0, "documento italiano")])

        results_en = store.search("tenant-1", "english", "en")
        results_it = store.search("tenant-1", "english", "it")

        assert len(results_en) == 1
        assert results_it == []


class TestBM25StoreRemoval:
    """Tests for document and tenant removal."""

    def test_remove_document(self) -> None:
        store = BM25Store()
        store.add_documents(
            "tenant-1",
            "en",
            [
                ("doc-1", 0, "first document"),
                ("doc-2", 0, "second document"),
            ],
        )

        removed = store.remove_document("tenant-1", "doc-1")
        assert removed == 1

        results = store.search("tenant-1", "first", "en")
        assert results == []

        results = store.search("tenant-1", "second", "en")
        assert len(results) == 1

    def test_remove_document_across_languages(self) -> None:
        store = BM25Store()
        store.add_documents("tenant-1", "en", [("doc-1", 0, "english text")])
        store.add_documents("tenant-1", "it", [("doc-1", 1, "testo italiano")])

        removed = store.remove_document("tenant-1", "doc-1")
        assert removed == 2

    def test_remove_nonexistent_document(self) -> None:
        store = BM25Store()
        removed = store.remove_document("tenant-1", "no-such-doc")
        assert removed == 0

    def test_clear_tenant(self) -> None:
        store = BM25Store()
        store.add_documents("tenant-1", "en", [("doc-1", 0, "data")])
        store.clear_tenant("tenant-1")

        results = store.search("tenant-1", "data", "en")
        assert results == []

    def test_clear_all(self) -> None:
        store = BM25Store()
        store.add_documents("tenant-1", "en", [("doc-1", 0, "data")])
        store.add_documents("tenant-2", "en", [("doc-2", 0, "more")])
        store.clear()

        assert store.search("tenant-1", "data", "en") == []
        assert store.search("tenant-2", "more", "en") == []
