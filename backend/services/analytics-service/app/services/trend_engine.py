"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Trend Engine — Long-term trend analysis and pattern detection.

Handles:
- Trend data retrieval and formatting
- Moving averages (N-day)
- Trend direction detection
- Historical data pagination
"""

from uuid import UUID

from app.repositories.repository import AnalyticsRepository
from sqlalchemy.ext.asyncio import AsyncSession


class TrendEngine:
    """Trend analysis engine."""

    def __init__(self, session: AsyncSession):
        self.repo = AnalyticsRepository(session)

    async def get_trend(
        self,
        user_id: UUID,
        metric_type: str,
        limit: int = 30,
        offset: int = 0,
    ) -> dict:
        """
        Get trend data for a metric with pagination.

        Returns:
            Dict with metric_type, values, labels, offset, limit
        """
        metrics = await self.repo.list_by_type(user_id, metric_type, limit + offset)

        # Apply offset
        metrics = metrics[offset : offset + limit]
        metrics.reverse()  # oldest first for charting

        return {
            "metric_type": metric_type,
            "values": [m.value for m in metrics],
            "labels": [m.created_at.strftime("%Y-%m-%d") for m in metrics],
            "offset": offset,
            "limit": limit,
        }

    async def get_moving_average(
        self,
        user_id: UUID,
        metric_type: str,
        days: int = 7,
    ) -> float:
        """
        Compute N-day moving average for a metric.

        Args:
            days: Number of days for moving average window
        """
        metrics = await self.repo.list_by_type(user_id, metric_type, limit=days)
        if not metrics:
            return 0.0
        return sum(m.value for m in metrics) / len(metrics)

    async def get_moving_average_series(
        self,
        user_id: UUID,
        metric_type: str,
        window_days: int = 7,
        limit: int = 30,
    ) -> dict:
        """
        Get moving average series over time.

        Args:
            window_days: Size of the moving average window
            limit: Number of data points to return
        """
        metrics = await self.repo.list_by_type(
            user_id, metric_type, limit=limit + window_days
        )
        if not metrics:
            return {
                "metric_type": metric_type,
                "window_days": window_days,
                "values": [],
                "labels": [],
            }

        # Compute moving averages
        moving_avgs = []
        labels = []
        for i in range(window_days - 1, len(metrics)):
            window = metrics[i - window_days + 1 : i + 1]
            avg = sum(m.value for m in window) / len(window)
            moving_avgs.append(avg)
            labels.append(metrics[i].created_at.strftime("%Y-%m-%d"))

        moving_avgs.reverse()
        labels.reverse()

        return {
            "metric_type": metric_type,
            "window_days": window_days,
            "values": moving_avgs[-limit:],
            "labels": labels[-limit:],
        }

    async def detect_trend_direction(
        self,
        user_id: UUID,
        metric_type: str,
        days: int = 7,
    ) -> dict:
        """
        Detect trend direction by comparing first and last values.

        Returns: "increasing", "decreasing", or "stable"
        """
        metrics = await self.repo.list_by_type(user_id, metric_type, limit=days)
        if len(metrics) < 2:
            return {
                "metric_type": metric_type,
                "direction": "insufficient_data",
                "change_percent": 0,
            }

        first_value = metrics[-1].value  # oldest
        last_value = metrics[0].value  # most recent

        if first_value == 0:
            change_percent = 0
        else:
            change_percent = ((last_value - first_value) / abs(first_value)) * 100

        # Determine direction with 10% threshold
        if change_percent > 10:
            direction = "increasing"
        elif change_percent < -10:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "metric_type": metric_type,
            "direction": direction,
            "change_percent": round(change_percent, 2),
            "first_value": first_value,
            "last_value": last_value,
            "period_days": days,
        }

    async def get_percentile(
        self,
        user_id: UUID,
        metric_type: str,
        percentile: float = 50,
        limit: int = 100,
    ) -> float:
        """
        Get percentile value for a metric.

        Args:
            percentile: Value between 0-100 (e.g., 50 for median, 95 for p95)
            limit: Number of recent values to consider
        """
        metrics = await self.repo.list_by_type(user_id, metric_type, limit=limit)
        if not metrics:
            return 0.0

        values = sorted([m.value for m in metrics])
        index = int((percentile / 100) * len(values))
        return values[min(index, len(values) - 1)]

    async def compare_periods(
        self,
        user_id: UUID,
        metric_type: str,
        current_days: int = 7,
        previous_days: int = 7,
    ) -> dict:
        """
        Compare metric performance between two periods.

        Returns: average and comparison metrics for both periods
        """
        # Get current period (most recent days)
        current_metrics = await self.repo.list_by_type(
            user_id, metric_type, limit=current_days
        )
        current_avg = (
            sum(m.value for m in current_metrics) / len(current_metrics)
            if current_metrics
            else 0
        )

        # Get previous period (next days after current)
        all_metrics = await self.repo.list_by_type(
            user_id, metric_type, limit=current_days + previous_days
        )
        previous_metrics = all_metrics[current_days : current_days + previous_days]
        previous_avg = (
            sum(m.value for m in previous_metrics) / len(previous_metrics)
            if previous_metrics
            else 0
        )

        change = current_avg - previous_avg
        change_percent = (change / abs(previous_avg) * 100) if previous_avg > 0 else 0

        return {
            "metric_type": metric_type,
            "current_period": {
                "days": current_days,
                "average": round(current_avg, 2),
            },
            "previous_period": {
                "days": previous_days,
                "average": round(previous_avg, 2),
            },
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
        }
