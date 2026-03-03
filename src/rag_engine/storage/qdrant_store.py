"""Qdrant vector store with per-tenant collection isolation."""

import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

logger = structlog.get_logger()


class QdrantStore:
    """Vector store backed by Qdrant with per-tenant collections.

    Each tenant gets a separate Qdrant collection, ensuring full
    data isolation. Points store document_id, chunk_index, and text
    as payload alongside the embedding vector.
    """

    def __init__(
        self,
        client: QdrantClient | None = None,
        url: str = "http://localhost:6333",
    ) -> None:
        """Initialize with a Qdrant client.

        Args:
            client: Pre-configured QdrantClient (e.g. in-memory for tests).
                If None, connects to the URL.
            url: Qdrant server URL (used only if client is None).
        """
        self._client = client or QdrantClient(url=url)

    def _collection_name(self, tenant_id: str) -> str:
        """Generate a collection name for a tenant."""
        return f"tenant_{tenant_id}"

    def ensure_collection(self, tenant_id: str, vector_size: int) -> None:
        """Create a collection for a tenant if it doesn't exist.

        Args:
            tenant_id: Tenant identifier.
            vector_size: Dimensionality of the embedding vectors.
        """
        collection_name = self._collection_name(tenant_id)

        existing = [c.name for c in self._client.get_collections().collections]
        if collection_name in existing:
            return

        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        logger.info(
            "qdrant_collection_created",
            tenant_id=tenant_id,
            collection=collection_name,
            vector_size=vector_size,
        )

    def add_documents(
        self,
        tenant_id: str,
        chunks: list[tuple[str, int, str, list[float]]],
    ) -> int:
        """Add document chunks with embeddings to the vector store.

        Args:
            tenant_id: Tenant identifier.
            chunks: List of (document_id, chunk_index, text, embedding) tuples.

        Returns:
            Number of points upserted.
        """
        if not chunks:
            return 0

        collection_name = self._collection_name(tenant_id)

        points = []
        for document_id, chunk_index, text, embedding in chunks:
            point_id = abs(hash(f"{document_id}:{chunk_index}")) % (2**63)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "text": text,
                    },
                )
            )

        self._client.upsert(
            collection_name=collection_name,
            points=points,
        )

        logger.info(
            "qdrant_documents_added",
            tenant_id=tenant_id,
            points_upserted=len(points),
        )

        return len(points)

    def search(
        self,
        tenant_id: str,
        query_vector: list[float],
        top_k: int = 10,
    ) -> list[tuple[str, int, str, float]]:
        """Search for similar vectors in a tenant's collection.

        Args:
            tenant_id: Tenant identifier.
            query_vector: Query embedding vector.
            top_k: Maximum number of results.

        Returns:
            List of (document_id, chunk_index, text, score) tuples,
            sorted by descending similarity.
        """
        collection_name = self._collection_name(tenant_id)

        existing = [c.name for c in self._client.get_collections().collections]
        if collection_name not in existing:
            return []

        hits = self._client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k,
        ).points

        results: list[tuple[str, int, str, float]] = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                (
                    payload.get("document_id", ""),
                    payload.get("chunk_index", 0),
                    payload.get("text", ""),
                    hit.score,
                )
            )

        return results

    def remove_document(self, tenant_id: str, document_id: str) -> int:
        """Remove all chunks of a document from the vector store.

        Args:
            tenant_id: Tenant identifier.
            document_id: Document to remove.

        Returns:
            Number of points removed (estimated).
        """
        collection_name = self._collection_name(tenant_id)

        existing = [c.name for c in self._client.get_collections().collections]
        if collection_name not in existing:
            return 0

        # Count points before deletion
        count_before = self._client.count(collection_name=collection_name).count

        self._client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )

        count_after = self._client.count(collection_name=collection_name).count
        removed = count_before - count_after

        if removed > 0:
            logger.info(
                "qdrant_document_removed",
                tenant_id=tenant_id,
                document_id=document_id,
                points_removed=removed,
            )

        return removed

    def clear_tenant(self, tenant_id: str) -> None:
        """Delete the entire collection for a tenant (GDPR right to erasure).

        Args:
            tenant_id: Tenant whose collection should be deleted.
        """
        collection_name = self._collection_name(tenant_id)

        existing = [c.name for c in self._client.get_collections().collections]
        if collection_name in existing:
            self._client.delete_collection(collection_name=collection_name)
            logger.info("qdrant_tenant_cleared", tenant_id=tenant_id)

    def clear(self) -> None:
        """Remove all tenant collections."""
        for collection in self._client.get_collections().collections:
            self._client.delete_collection(collection_name=collection.name)
        logger.info("qdrant_all_cleared")
