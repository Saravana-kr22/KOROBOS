"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Metrics Engine — Core metric recording and immediate analysis.

Handles:
- Recording individual metric events
- Retrieving latest/average metrics by type
- Computing basic statistics (min, max, avg, latest)
"""

from uuid import UUID

from app.repositories.repository import AnalyticsRepository
from sqlalchemy.ext.asyncio import AsyncSession


class MetricsEngine:
    """Core metrics operations engine."""

    def __init__(self, session: AsyncSession):
        self.repo = AnalyticsRepository(session)

    async def record_metric(
        self,
        user_id: UUID,
        metric_type: str,
        value: float,
        metadata: dict = None,
    ):
        """Record a single metric value."""
        return await self.repo.create(user_id, metric_type, value, metadata)

    async def get_latest_metric(
        self,
        user_id: UUID,
        metric_type: str,
    ):
        """Get the most recent value for a metric type."""
        return await self.repo.get_latest(user_id, metric_type)

    async def get_average_metric(
        self,
        user_id: UUID,
        metric_type: str,
    ) -> float:
        """Get average value for a metric type across all time."""
        return await self.repo.get_average(user_id, metric_type)

    async def get_metric_by_type(
        self,
        user_id: UUID,
        metric_type: str,
        limit: int = 30,
    ):
        """Get metrics of a specific type."""
        return await self.repo.list_by_type(user_id, metric_type, limit)

    async def get_metric_range(
        self,
        user_id: UUID,
        metric_type: str,
        days: int = 30,
    ):
        """Get metrics within a date range (last N days)."""
        return await self.repo.get_range(user_id, metric_type, days)

    async def compute_daily_stats(
        self,
        user_id: UUID,
        metric_type: str,
    ) -> dict:
        """Compute daily statistics for a metric."""
        metrics = await self.repo.list_by_type(user_id, metric_type, limit=100)

        if not metrics:
            return {
                "metric_type": metric_type,
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "latest": 0,
            }

        values = [m.value for m in metrics]
        return {
            "metric_type": metric_type,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[0] if values else 0,
        }
