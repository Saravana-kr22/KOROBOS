"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from backend.shared.messaging.schemas import BaseEvent


class MealLoggedEvent(BaseEvent):
    event_type: str = "meal.logged"
    source_service: str = "health-service"


class WorkoutLoggedEvent(BaseEvent):
    event_type: str = "workout.logged"
    source_service: str = "health-service"
