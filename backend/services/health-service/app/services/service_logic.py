"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repository import HealthRepository
from app.schemas.schema import MealLogCreate, WorkoutLogCreate

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import send_event

logger = get_logger("health-service.logic")


class HealthService:
    def __init__(self, session: AsyncSession):
        self.repo = HealthRepository(session)

    async def log_meal(self, user_id: UUID, data: MealLogCreate):
        log = await self.repo.create(user_id=user_id, log_type="meal", calories=data.calories, description=data.description or "")
        try:
            await send_event("meal.logged", {"event": "meal.logged", "payload": {"log_id": str(log.id), "user_id": str(user_id), "calories": data.calories}}, key=str(user_id))
        except Exception as exc:
            logger.warning(f"Failed to publish meal.logged: {exc}")
        return log

    async def log_workout(self, user_id: UUID, data: WorkoutLogCreate):
        log = await self.repo.create(user_id=user_id, log_type="workout", duration=data.duration, calories=data.calories or 0, description=data.description or "")
        try:
            await send_event("workout.logged", {"event": "workout.logged", "payload": {"log_id": str(log.id), "user_id": str(user_id), "duration": data.duration}}, key=str(user_id))
        except Exception as exc:
            logger.warning(f"Failed to publish workout.logged: {exc}")
        return log

    async def list_logs(self, user_id: UUID, log_type=None, offset=0, limit=50):
        return await self.repo.list_by_user(user_id, log_type, offset, limit)

    async def get_stats(self, user_id: UUID):
        return await self.repo.get_stats(user_id)
