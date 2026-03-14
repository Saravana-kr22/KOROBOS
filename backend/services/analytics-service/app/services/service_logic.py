"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID

from app.repositories.repository import AnalyticsRepository
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.repo = AnalyticsRepository(session)

    async def record_metric(
        self, user_id: UUID, metric_type: str, value: float, metadata: dict = None
    ):
        return await self.repo.create(user_id, metric_type, value, metadata)

    async def get_productivity(self, user_id: UUID) -> dict:
        productivity = await self.repo.get_average(user_id, "productivity_score")
        consistency = await self.repo.get_average(user_id, "habit_consistency")
        learning = await self.repo.get_average(user_id, "learning_hours")
        return {
            "productivity_score": round(productivity, 2),
            "habit_consistency": round(consistency, 2),
            "learning_hours": round(learning, 2),
        }

    async def get_trend(self, user_id: UUID, metric_type: str, limit: int = 30) -> dict:
        metrics = await self.repo.list_by_type(user_id, metric_type, limit)
        metrics.reverse()  # oldest first for charting
        return {
            "metric_type": metric_type,
            "values": [m.value for m in metrics],
            "labels": [m.created_at.strftime("%Y-%m-%d") for m in metrics],
        }
