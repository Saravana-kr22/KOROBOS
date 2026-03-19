"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Kafka event definitions for the Learning Service.

.. deprecated:: Re-export shim — import from ``learning_events`` directly.
"""

# Re-export from canonical location
from app.events.learning_events import (  # noqa: F401
    LearningSessionCompletedEvent,
    LearningSessionLoggedEvent,
    LearningSessionStartedEvent,
    LearningTopicCreatedEvent,
)

from backend.shared.messaging.schemas import BaseEvent  # noqa: F401
