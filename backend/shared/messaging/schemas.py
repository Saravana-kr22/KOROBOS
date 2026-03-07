"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base schema for all CortexOS Kafka events."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(..., description="Type of event, e.g. 'note.created'")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_service: str = Field(..., description="Service that emitted the event")
    correlation_id: Optional[str] = Field(
        default=None, description="Request correlation ID for tracing"
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Event-specific data"
    )
