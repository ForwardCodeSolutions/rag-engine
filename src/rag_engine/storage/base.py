"""Abstract base class for storage backends."""

from abc import ABC, abstractmethod


class BaseStore(ABC):
    """Common interface for all storage backends.

    Each store must support per-tenant document management
    and GDPR-compliant data erasure.
    """

    @abstractmethod
    def remove_document(self, tenant_id: str, document_id: str) -> int:
        """Remove all chunks of a document.

        Args:
            tenant_id: Tenant identifier.
            document_id: Document to remove.

        Returns:
            Number of items removed.
        """

    @abstractmethod
    def clear_tenant(self, tenant_id: str) -> int:
        """Remove all data for a tenant (GDPR right to erasure).

        Args:
            tenant_id: Tenant whose data should be deleted.

        Returns:
            Number of items removed.
        """

    @abstractmethod
    def clear(self) -> None:
        """Remove all data from the store."""
