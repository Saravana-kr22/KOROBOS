"""
KOROBOS — Database Service Events

Kafka event definitions for database operations.
"""

from backend.shared.messaging.schemas import BaseEvent


class DatabaseCreatedEvent(BaseEvent):
    """Event published when a database is created."""

    event_type: str = "database.created"
    source_service: str = "database-service"


class RecordCreatedEvent(BaseEvent):
    """Event published when a record is created."""

    event_type: str = "record.created"
    source_service: str = "database-service"


class RecordUpdatedEvent(BaseEvent):
    """Event published when a record is updated."""

    event_type: str = "record.updated"
    source_service: str = "database-service"


class RecordDeletedEvent(BaseEvent):
    """Event published when a record is deleted."""

    event_type: str = "record.deleted"
    source_service: str = "database-service"
