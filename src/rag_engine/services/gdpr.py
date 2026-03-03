"""GDPR compliance service for data management."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore
from rag_engine.utils.audit import log_operation

if TYPE_CHECKING:
    from rag_engine.storage.qdrant_store import QdrantStore

logger = structlog.get_logger()


class GDPRService:
    """Service for GDPR-compliant data operations.

    Handles cascading deletions across all storage backends
    (BM25, Knowledge Graph, Qdrant) with full audit logging.
    """

    def __init__(
        self,
        bm25_store: BM25Store,
        graph_store: KnowledgeGraphStore,
        qdrant_store: QdrantStore | None = None,
    ) -> None:
        """Initialize with storage backends.

        Args:
            bm25_store: BM25 keyword search index.
            graph_store: Knowledge graph store.
            qdrant_store: Qdrant vector store (optional).
        """
        self.bm25_store = bm25_store
        self.graph_store = graph_store
        self.qdrant_store = qdrant_store

    def delete_document(
        self,
        tenant_id: str,
        document_id: str,
        reason: str = "user request",
    ) -> dict[str, int]:
        """Delete a document from all storage backends.

        Args:
            tenant_id: Tenant owning the document.
            document_id: Document to delete.
            reason: Reason for deletion (audit trail).

        Returns:
            Dictionary with counts of removed items per backend.
        """
        bm25_removed = self.bm25_store.remove_document(tenant_id, document_id)
        graph_removed = self.graph_store.remove_document(tenant_id, document_id)
        vector_removed = 0
        if self.qdrant_store is not None:
            vector_removed = self.qdrant_store.remove_document(tenant_id, document_id)

        log_operation(
            operation="delete",
            tenant_id=tenant_id,
            resource_type="document",
            resource_id=document_id,
            reason=reason,
            details={
                "bm25_chunks_removed": bm25_removed,
                "graph_chunks_removed": graph_removed,
                "vector_chunks_removed": vector_removed,
            },
        )

        logger.info(
            "document_deleted",
            tenant_id=tenant_id,
            document_id=document_id,
            bm25_removed=bm25_removed,
            graph_removed=graph_removed,
            vector_removed=vector_removed,
        )

        return {
            "bm25_chunks_removed": bm25_removed,
            "graph_chunks_removed": graph_removed,
            "vector_chunks_removed": vector_removed,
        }

    def delete_tenant_data(
        self,
        tenant_id: str,
        reason: str = "GDPR right to erasure",
    ) -> None:
        """Delete ALL data for a tenant across all storage backends.

        This implements GDPR Article 17 (Right to Erasure). All data
        belonging to the tenant is permanently removed.

        Args:
            tenant_id: Tenant whose data should be deleted.
            reason: Reason for deletion (audit trail).
        """
        self.bm25_store.clear_tenant(tenant_id)
        self.graph_store.clear_tenant(tenant_id)
        if self.qdrant_store is not None:
            self.qdrant_store.clear_tenant(tenant_id)

        log_operation(
            operation="delete_all",
            tenant_id=tenant_id,
            resource_type="tenant",
            resource_id=tenant_id,
            reason=reason,
        )

        logger.info("tenant_data_deleted", tenant_id=tenant_id, reason=reason)
