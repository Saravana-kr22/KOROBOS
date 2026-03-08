"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from typing import Optional
from uuid import UUID

from app.models.model import HealthLog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class HealthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        log_type: str,
        calories: int = 0,
        duration: int = 0,
        description: str = "",
    ) -> HealthLog:
        obj = HealthLog(
            user_id=user_id,
            log_type=log_type,
            calories=calories,
            duration=duration,
            description=description,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_id(self, log_id: UUID) -> Optional[HealthLog]:
        result = await self.session.execute(
            select(HealthLog).where(HealthLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        log_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[HealthLog], int]:
        q = select(HealthLog).where(HealthLog.user_id == user_id)
        count_q = (
            select(func.count())
            .select_from(HealthLog)
            .where(HealthLog.user_id == user_id)
        )
        if log_type:
            q = q.where(HealthLog.log_type == log_type)
            count_q = count_q.where(HealthLog.log_type == log_type)
        total = (await self.session.execute(count_q)).scalar_one()
        result = await self.session.execute(
            q.order_by(HealthLog.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def delete(self, obj: HealthLog) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def get_stats(self, user_id: UUID) -> dict:
        meals_q = (
            select(func.count())
            .select_from(HealthLog)
            .where(HealthLog.user_id == user_id, HealthLog.log_type == "meal")
        )
        meals = (await self.session.execute(meals_q)).scalar_one()

        workouts_q = (
            select(func.count())
            .select_from(HealthLog)
            .where(HealthLog.user_id == user_id, HealthLog.log_type == "workout")
        )
        workouts = (await self.session.execute(workouts_q)).scalar_one()

        cal_q = select(
            func.coalesce(func.sum(HealthLog.calories), 0)
        ).where(HealthLog.user_id == user_id)
        total_cal = (await self.session.execute(cal_q)).scalar_one()

        dur_q = select(
            func.coalesce(func.sum(HealthLog.duration), 0)
        ).where(
            HealthLog.user_id == user_id,
            HealthLog.log_type == "workout",
        )
        total_dur = (await self.session.execute(dur_q)).scalar_one()

        return {
            "total_meals": meals,
            "total_workouts": workouts,
            "total_calories": total_cal,
            "total_workout_minutes": total_dur,
        }
