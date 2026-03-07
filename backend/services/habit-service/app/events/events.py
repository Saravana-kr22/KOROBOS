"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Kafka event definitions for the Habit Service.
"""

from backend.shared.messaging.schemas import BaseEvent


class HabitCreatedEvent(BaseEvent):
    event_type: str = "habit.created"
    source_service: str = "habit-service"


class HabitCompletedEvent(BaseEvent):
    event_type: str = "habit.completed"
    source_service: str = "habit-service"
