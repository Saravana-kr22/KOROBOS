"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Audit Log Utility — standardized logging for security-sensitive actions.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from backend.shared.logging.logger import get_logger

logger = get_logger("audit-log")


def log_audit_event(
    event_type: str,
    user_id: Optional[UUID] = None,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    status: str = "success",
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log a structured audit event for security and compliance.

    Args:
        event_type: Category of the event (e.g., 'auth.login', 'data.delete').
        user_id: UUID of the user performing the action.
        resource_id: ID of the resource being accessed/modified.
        resource_type: Type of the resource (e.g., 'note', 'habit').
        action: Specific action performed (e.g., 'update', 'view').
        status: 'success' or 'failure'.
        metadata: Additional contextual data.
    """
    audit_data = {
        "audit": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user_id": str(user_id) if user_id else None,
        "resource_id": resource_id,
        "resource_type": resource_type,
        "action": action,
        "status": status,
        "metadata": metadata or {},
    }

    # Structured logging automatically includes these fields in the JSON output
    logger.info(
        f"Audit: {event_type} - {action or ''} on {resource_type or ''} ({status})",
        extra=audit_data,
    )
