"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Kafka event definitions for the Notes Service.
"""

from backend.shared.messaging.schemas import BaseEvent


class NoteCreatedEvent(BaseEvent):
    """Event emitted when a note is created."""

    event_type: str = "note.created"
    source_service: str = "notes-service"


class NoteUpdatedEvent(BaseEvent):
    """Event emitted when a note is updated."""

    event_type: str = "note.updated"
    source_service: str = "notes-service"


class NoteLinkCreatedEvent(BaseEvent):
    """Event emitted when a link between notes is created."""

    event_type: str = "note.link.created"
    source_service: str = "notes-service"
