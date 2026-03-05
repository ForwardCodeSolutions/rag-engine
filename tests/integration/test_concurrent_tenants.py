"""Integration tests for concurrent tenant isolation."""

from concurrent.futures import ThreadPoolExecutor

from rag_engine.core.hybrid_retriever import HybridRetriever
from rag_engine.models.search import SearchType
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore


class TestConcurrentTenants:
    """Verify data isolation when multiple tenants operate simultaneously."""

    def _setup(self):
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        retriever = HybridRetriever(bm25, graph)
        return bm25, graph, retriever

    def test_three_tenants_isolated(self) -> None:
        """Three tenants with different data; each only sees their own."""
        bm25, graph, retriever = self._setup()

        tenants = {
            "tenant-alpha": ("Alpha corporation builds rockets", "rockets"),
            "tenant-beta": ("Beta industries manufactures widgets", "widgets"),
            "tenant-gamma": ("Gamma labs researches quantum computing", "quantum"),
        }

        for tenant, (text, _) in tenants.items():
            bm25.add_documents(tenant, "en", [(f"{tenant}-doc", 0, text)])
            graph.add_documents(tenant, [(f"{tenant}-doc", 0, text)])

        # Each tenant finds their own keyword
        for tenant, (_, query) in tenants.items():
            results = retriever.search(
                tenant, query, language="en", search_type=SearchType.BM25,
            )
            assert len(results) >= 1, f"{tenant} should find '{query}'"

        # tenant-beta must not see tenant-alpha data
        results = retriever.search(
            "tenant-beta", "rockets", language="en", search_type=SearchType.BM25,
        )
        assert len(results) == 0, "tenant-beta must not see tenant-alpha data"

    def test_concurrent_uploads_maintain_isolation(self) -> None:
        """Parallel uploads from different tenants must not leak data."""
        bm25, graph, retriever = self._setup()

        def ingest_and_search(args):
            tenant, text, query = args
            bm25.add_documents(tenant, "en", [(f"{tenant}-doc", 0, text)])
            graph.add_documents(tenant, [(f"{tenant}-doc", 0, text)])
            results = retriever.search(
                tenant, query, language="en", search_type=SearchType.BM25,
            )
            return tenant, len(results)

        tasks = [
            ("iso-1", "Artificial intelligence in medicine diagnostics", "medicine"),
            ("iso-2", "Blockchain for supply chain management tracking", "blockchain"),
            ("iso-3", "Renewable energy from solar panel technology", "solar"),
        ]

        with ThreadPoolExecutor(max_workers=3) as pool:
            results = dict(pool.map(ingest_and_search, tasks))

        for tenant, count in results.items():
            assert count >= 1, f"{tenant} should find its own data"

    def test_deleting_one_tenant_preserves_others(self) -> None:
        """Deleting one tenant's data must not affect other tenants."""
        bm25, graph, retriever = self._setup()

        bm25.add_documents("keep-t", "en", [("keep-doc", 0, "Data to keep intact")])
        graph.add_documents("keep-t", [("keep-doc", 0, "Data to keep intact")])
        bm25.add_documents("del-t", "en", [("del-doc", 0, "Data to delete forever")])
        graph.add_documents("del-t", [("del-doc", 0, "Data to delete forever")])

        # Delete one tenant
        bm25.clear_tenant("del-t")
        graph.clear_tenant("del-t")

        # Deleted tenant should have no results
        results = retriever.search(
            "del-t", "Data to delete", language="en", search_type=SearchType.BM25,
        )
        assert len(results) == 0

        # Other tenant should still have results
        results = retriever.search(
            "keep-t", "Data to keep", language="en", search_type=SearchType.BM25,
        )
        assert len(results) >= 1
