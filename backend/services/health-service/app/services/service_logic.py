"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID

from app.events.events import MealLoggedEvent, WorkoutLoggedEvent
from app.repositories.repository import HealthRepository
from app.schemas.schema import MealLogCreate, WorkoutLogCreate
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.messaging.producer import publish_event


class HealthService:
    def __init__(self, session: AsyncSession):
        self.repo = HealthRepository(session)

    async def log_meal(self, user_id: UUID, data: MealLogCreate):
        log = await self.repo.create(
            user_id=user_id,
            log_type="meal",
            calories=data.calories,
            description=data.description or "",
            food_name=data.food_name,
            protein=data.protein,
            carbs=data.carbs,
            fat=data.fat,
        )
        event = MealLoggedEvent(
            payload={
                "meal_id": str(log.id),
                "user_id": str(user_id),
                "calories": data.calories,
                "description": data.description or "",
                "food_name": data.food_name,
                "protein": data.protein,
                "carbs": data.carbs,
                "fat": data.fat,
            }
        )
        await publish_event(event, key=str(user_id))
        return log

    async def log_workout(self, user_id: UUID, data: WorkoutLogCreate):
        log = await self.repo.create(
            user_id=user_id,
            log_type="workout",
            duration=data.duration,
            calories=data.calories or 0,
            description=data.description or "",
            workout_type=data.workout_type,
        )
        event = WorkoutLoggedEvent(
            payload={
                "workout_id": str(log.id),
                "user_id": str(user_id),
                "duration": data.duration,
                "calories": data.calories or 0,
                "description": data.description or "",
                "workout_type": data.workout_type,
            }
        )
        await publish_event(event, key=str(user_id))
        return log

    async def list_logs(self, user_id: UUID, log_type=None, offset=0, limit=50):
        return await self.repo.list_by_user(user_id, log_type, offset, limit)

    async def get_stats(self, user_id: UUID):
        return await self.repo.get_stats(user_id)

    async def delete_log(self, user_id: UUID, log_id: UUID) -> bool:
        """Delete a health log, validating user ownership."""
        log = await self.repo.get_by_id(log_id)
        if not log or log.user_id != user_id:
            return None
        await self.repo.delete(log)
        return True

    async def get_daily_stats(self, user_id: UUID, date=None):
        """Get daily calorie stats for a given date (defaults to today)."""
        return await self.repo.get_daily_stats(user_id, date)
