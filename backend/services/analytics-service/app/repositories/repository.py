"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import AnalyticsMetric


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, metric_type: str, value: float, metadata_json: dict = None) -> AnalyticsMetric:
        obj = AnalyticsMetric(user_id=user_id, metric_type=metric_type, value=value, metadata_json=metadata_json or {})
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_latest(self, user_id: UUID, metric_type: str) -> Optional[AnalyticsMetric]:
        q = select(AnalyticsMetric).where(
            AnalyticsMetric.user_id == user_id,
            AnalyticsMetric.metric_type == metric_type,
        ).order_by(AnalyticsMetric.created_at.desc()).limit(1)
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def list_by_type(self, user_id: UUID, metric_type: str, limit: int = 30) -> list[AnalyticsMetric]:
        q = select(AnalyticsMetric).where(
            AnalyticsMetric.user_id == user_id,
            AnalyticsMetric.metric_type == metric_type,
        ).order_by(AnalyticsMetric.created_at.desc()).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_average(self, user_id: UUID, metric_type: str) -> float:
        q = select(func.coalesce(func.avg(AnalyticsMetric.value), 0.0)).where(
            AnalyticsMetric.user_id == user_id,
            AnalyticsMetric.metric_type == metric_type,
        )
        return (await self.session.execute(q)).scalar_one()
