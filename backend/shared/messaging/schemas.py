"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from backend.shared.logging.logger import get_correlation_id
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class BaseEvent(BaseModel):
    """Base schema for all CortexOS Kafka events."""

    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(..., description="Type of event, e.g. 'note.created'")
    schema_version: int = Field(default=1, ge=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = Field(
        default_factory=get_correlation_id,
        description="Request correlation ID for tracing",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Event-specific data"
    )

    source_service: str = Field(
        ...,
        description="Service that emitted the event",
        validation_alias=AliasChoices("source_service", "producer"),
        serialization_alias="producer",
    )
