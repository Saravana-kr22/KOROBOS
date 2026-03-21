"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Repository — data access layer.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.models.model import AnalyticsMetric
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        metric_type: str,
        value: float,
        metadata_json: dict = None,
    ) -> AnalyticsMetric:
        """Create a new analytics metric record."""
        obj = AnalyticsMetric(
            user_id=user_id,
            metric_type=metric_type,
            value=value,
            metadata_json=metadata_json or {},
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_latest(
        self, user_id: UUID, metric_type: str
    ) -> Optional[AnalyticsMetric]:
        """Get the most recent metric of a type."""
        q = (
            select(AnalyticsMetric)
            .where(
                AnalyticsMetric.user_id == user_id,
                AnalyticsMetric.metric_type == metric_type,
            )
            .order_by(AnalyticsMetric.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def list_by_type(
        self, user_id: UUID, metric_type: str, limit: int = 30
    ) -> list[AnalyticsMetric]:
        """Get recent metrics of a type."""
        q = (
            select(AnalyticsMetric)
            .where(
                AnalyticsMetric.user_id == user_id,
                AnalyticsMetric.metric_type == metric_type,
            )
            .order_by(AnalyticsMetric.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_average(self, user_id: UUID, metric_type: str) -> float:
        """Get average value for a metric type."""
        q = select(func.coalesce(func.avg(AnalyticsMetric.value), 0.0)).where(
            AnalyticsMetric.user_id == user_id,
            AnalyticsMetric.metric_type == metric_type,
        )
        return (await self.session.execute(q)).scalar_one()

    async def get_range(
        self, user_id: UUID, metric_type: str, days: int = 7
    ) -> list[AnalyticsMetric]:
        """Get metrics from last N days."""
        start_date = datetime.utcnow() - timedelta(days=days)
        q = (
            select(AnalyticsMetric)
            .where(
                AnalyticsMetric.user_id == user_id,
                AnalyticsMetric.metric_type == metric_type,
                AnalyticsMetric.created_at >= start_date,
            )
            .order_by(AnalyticsMetric.created_at.asc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_range_between(
        self, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> list[AnalyticsMetric]:
        """Get all metrics for a user between two dates."""
        q = (
            select(AnalyticsMetric)
            .where(
                AnalyticsMetric.user_id == user_id,
                AnalyticsMetric.created_at >= start_date,
                AnalyticsMetric.created_at < end_date,
            )
            .order_by(AnalyticsMetric.created_at.asc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())
