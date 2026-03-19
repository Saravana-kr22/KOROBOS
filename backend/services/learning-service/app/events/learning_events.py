"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Kafka event definitions for the Learning Service.
"""

from backend.shared.messaging.schemas import BaseEvent


class LearningSessionLoggedEvent(BaseEvent):
    """Emitted when a learning session is manually logged."""

    event_type: str = "learning.session.logged"
    source_service: str = "learning-service"


class LearningSessionStartedEvent(BaseEvent):
    """Emitted when a timer session is started."""

    event_type: str = "learning.session.started"
    source_service: str = "learning-service"
    # payload: session_id, user_id, topic, start_time


class LearningSessionCompletedEvent(BaseEvent):
    """Emitted when a timer session is stopped/completed."""

    event_type: str = "learning.session.completed"
    source_service: str = "learning-service"
    # payload: session_id, user_id, topic, duration, start_time, end_time


class LearningTopicCreatedEvent(BaseEvent):
    """Emitted when a new topic is created."""

    event_type: str = "learning.topic.created"
    source_service: str = "learning-service"
    # payload: topic_id, user_id, name
