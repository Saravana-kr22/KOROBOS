"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from backend.shared.messaging.schemas import BaseEvent


class LearningSessionLoggedEvent(BaseEvent):
    event_type: str = "learning.session.logged"
    source_service: str = "learning-service"
