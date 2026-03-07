"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from backend.shared.messaging.schemas import BaseEvent


class AIInteractionCompletedEvent(BaseEvent):
    event_type: str = "ai.interaction.completed"
    source_service: str = "ai-service"
