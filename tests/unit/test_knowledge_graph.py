"""Tests for knowledge graph store."""

from rag_engine.storage.knowledge_graph import (
    KnowledgeGraphStore,
    extract_entities,
)


class TestExtractEntities:
    """Tests for entity extraction."""

    def test_extracts_capitalized_phrases(self) -> None:
        text = "The European Union signed a treaty with the United States."
        entities = extract_entities(text)
        assert "European Union" in entities
        assert "United States" in entities

    def test_extracts_single_capitalized_words(self) -> None:
        text = "Alice met Bob at the conference."
        entities = extract_entities(text)
        assert "Alice" in entities
        assert "Bob" in entities

    def test_filters_short_words(self) -> None:
        entities = extract_entities("An example.")
        assert "An" not in entities

    def test_empty_text(self) -> None:
        assert extract_entities("") == []

    def test_no_entities_in_lowercase(self) -> None:
        assert extract_entities("all lowercase text here") == []

    def test_deduplicates(self) -> None:
        text = "Alice met Alice again."
        entities = extract_entities(text)
        assert entities.count("Alice") == 1


class TestKnowledgeGraphAddAndSearch:
    """Tests for adding documents and searching the graph."""

    def test_add_and_search_by_entity(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice works at Acme Corporation in Berlin."),
            ],
        )

        results = store.search("tenant-1", "Alice")
        assert len(results) == 1
        assert results[0][0] == "doc-1"
        assert results[0][3] > 0

    def test_search_finds_related_chunks(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice works at Acme Corporation."),
                ("doc-1", 1, "Acme Corporation is based in Berlin."),
                ("doc-2", 0, "Bob lives in Paris."),
            ],
        )

        results = store.search("tenant-1", "Acme")
        doc_ids = [r[0] for r in results]
        assert "doc-1" in doc_ids
        assert len(results) == 2  # both chunks mention Acme

    def test_search_scores_multiple_entity_matches_higher(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice works at Acme Corporation in Berlin."),
                ("doc-2", 0, "Bob lives in Berlin."),
            ],
        )

        results = store.search("tenant-1", "Alice Berlin")
        # doc-1 matches both Alice and Berlin, should score higher
        assert results[0][0] == "doc-1"
        assert results[0][3] > results[1][3]

    def test_search_respects_top_k(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice in Berlin."),
                ("doc-2", 0, "Bob in Berlin."),
                ("doc-3", 0, "Charlie in Berlin."),
            ],
        )

        results = store.search("tenant-1", "Berlin", top_k=2)
        assert len(results) <= 2

    def test_search_empty_graph(self) -> None:
        store = KnowledgeGraphStore()
        assert store.search("tenant-1", "anything") == []

    def test_search_no_matching_entities(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice works at Acme."),
            ],
        )
        results = store.search("tenant-1", "xyz")
        assert results == []

    def test_search_empty_query(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents("tenant-1", [("doc-1", 0, "Alice.")])
        assert store.search("tenant-1", "") == []

    def test_add_returns_entity_count(self) -> None:
        store = KnowledgeGraphStore()
        count = store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice met Bob."),
            ],
        )
        assert count >= 2


class TestKnowledgeGraphTenantIsolation:
    """Tests for per-tenant isolation."""

    def test_tenants_are_isolated(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents("tenant-1", [("doc-1", 0, "Alice works here.")])
        store.add_documents("tenant-2", [("doc-2", 0, "Bob works there.")])

        results_t1 = store.search("tenant-1", "Alice")
        results_t2 = store.search("tenant-2", "Alice")

        assert len(results_t1) == 1
        assert results_t2 == []


class TestKnowledgeGraphRemoval:
    """Tests for document and tenant removal."""

    def test_remove_document(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice works at Acme."),
                ("doc-2", 0, "Bob works at Acme."),
            ],
        )

        removed = store.remove_document("tenant-1", "doc-1")
        assert removed == 1

        results = store.search("tenant-1", "Alice")
        assert results == []

        results = store.search("tenant-1", "Bob")
        assert len(results) == 1

    def test_remove_cleans_orphaned_entities(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice works alone."),
            ],
        )

        store.remove_document("tenant-1", "doc-1")
        graph = store._graphs["tenant-1"]
        # Alice entity should be removed since no chunks reference it
        entity_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "entity"]
        assert len(entity_nodes) == 0

    def test_remove_nonexistent_document(self) -> None:
        store = KnowledgeGraphStore()
        assert store.remove_document("tenant-1", "no-such-doc") == 0

    def test_clear_tenant(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents("tenant-1", [("doc-1", 0, "Alice.")])
        store.clear_tenant("tenant-1")
        assert store.search("tenant-1", "Alice") == []

    def test_clear_all(self) -> None:
        store = KnowledgeGraphStore()
        store.add_documents("tenant-1", [("doc-1", 0, "Alice.")])
        store.add_documents("tenant-2", [("doc-2", 0, "Bob.")])
        store.clear()
        assert store.search("tenant-1", "Alice") == []
        assert store.search("tenant-2", "Bob") == []
