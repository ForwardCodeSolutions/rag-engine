"""Audit logging for GDPR-relevant operations."""

from datetime import UTC, datetime

import structlog

audit_logger = structlog.get_logger("audit")


def log_operation(
    operation: str,
    tenant_id: str,
    resource_type: str,
    resource_id: str | None = None,
    reason: str | None = None,
    details: dict | None = None,
) -> None:
    """Log a GDPR-relevant data operation for audit trail.

    Args:
        operation: Type of operation (create, read, delete, search).
        tenant_id: Tenant performing the operation.
        resource_type: Type of resource affected (document, tenant).
        resource_id: Identifier of the affected resource.
        reason: Reason for the operation (required for deletions).
        details: Additional context for the operation.
    """
    audit_logger.info(
        "audit_event",
        operation=operation,
        tenant_id=tenant_id,
        resource_type=resource_type,
        resource_id=resource_id,
        reason=reason,
        details=details or {},
        timestamp=datetime.now(tz=UTC).isoformat(),
    )
