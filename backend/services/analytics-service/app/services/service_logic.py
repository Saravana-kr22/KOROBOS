"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service business logic — Orchestrates modular components.

High-level service that coordinates:
- MetricsEngine: Core metric operations
- TrendEngine: Trend analysis and patterns
- AggregationService: Cross-domain aggregation
- ClickHouseRepository: Long-term historical analysis
"""

import json
from uuid import UUID

from app.repositories.clickhouse_repository import ClickHouseRepository
from app.services.aggregation_service import AggregationService
from app.services.metrics_engine import MetricsEngine
from app.services.trend_engine import TrendEngine
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsService:
    """
    Orchestrator service coordinating modular analytics engines.

    Delegates to specialized engines:
    - metrics: Core metric recording and retrieval
    - trends: Trend analysis and moving averages
    - aggregation: Cross-domain scoring and overview
    - clickhouse: Long-term historical analysis (optional)
    """

    def __init__(
        self,
        session: AsyncSession,
        redis=None,
        clickhouse_repo: ClickHouseRepository = None,
    ):
        self.session = session
        self.redis = redis
        self.cache_ttl = 300  # 5 minutes in seconds

        # Initialize modular engines
        self.metrics = MetricsEngine(session)
        self.trends = TrendEngine(session)
        self.aggregation = AggregationService(session)
        self.clickhouse = clickhouse_repo

    async def _get_cached(self, key: str):
        """Retrieve value from cache if available."""
        if not self.redis:
            return None
        try:
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # Graceful degradation on cache errors
        return None

    async def _set_cached(self, key: str, value: dict, ttl: int = None):
        """Store value in cache with TTL."""
        if not self.redis:
            return
        try:
            ttl = ttl or self.cache_ttl
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception:
            pass  # Graceful degradation on cache errors

    # ──────────────────────────────────────────────────────────────────────────────
    # Metrics API (delegates to MetricsEngine)
    # ──────────────────────────────────────────────────────────────────────────────

    async def record_metric(
        self, user_id: UUID, metric_type: str, value: float, metadata: dict = None
    ):
        """Record a metric for a user."""
        # Invalidate relevant caches on new metric
        if self.redis:
            try:
                await self.redis.delete(f"analytics:overview:{user_id}")
            except Exception:
                pass
        return await self.metrics.record_metric(user_id, metric_type, value, metadata)

    async def get_latest_metric(self, user_id: UUID, metric_type: str):
        """Get the most recent value for a metric type."""
        return await self.metrics.get_latest_metric(user_id, metric_type)

    async def get_average_metric(self, user_id: UUID, metric_type: str) -> float:
        """Get average value for a metric type."""
        return await self.metrics.get_average_metric(user_id, metric_type)

    # ──────────────────────────────────────────────────────────────────────────────
    # Trend API (delegates to TrendEngine)
    # ──────────────────────────────────────────────────────────────────────────────

    async def get_trend(
        self,
        user_id: UUID,
        metric_type: str,
        limit: int = 30,
        offset: int = 0,
    ) -> dict:
        """Get trend data for a metric with pagination support and caching."""
        cache_key = f"analytics:trend:{user_id}:{metric_type}:{limit}:{offset}"

        # Check cache first
        cached_data = await self._get_cached(cache_key)
        if cached_data:
            return cached_data

        # Fetch from trend engine
        result = await self.trends.get_trend(user_id, metric_type, limit, offset)

        # Cache the result
        await self._set_cached(cache_key, result)

        return result

    async def get_moving_average(
        self, user_id: UUID, metric_type: str, days: int = 7
    ) -> float:
        """Compute N-day moving average for a metric."""
        return await self.trends.get_moving_average(user_id, metric_type, days)

    async def get_moving_average_series(
        self,
        user_id: UUID,
        metric_type: str,
        window_days: int = 7,
        limit: int = 30,
    ) -> dict:
        """Get moving average series over time."""
        return await self.trends.get_moving_average_series(
            user_id, metric_type, window_days, limit
        )

    async def detect_trend_direction(
        self, user_id: UUID, metric_type: str, days: int = 7
    ) -> dict:
        """Detect trend direction (increasing, decreasing, stable)."""
        return await self.trends.detect_trend_direction(user_id, metric_type, days)

    async def get_percentile(
        self,
        user_id: UUID,
        metric_type: str,
        percentile: float = 50,
        limit: int = 100,
    ) -> float:
        """Get percentile value for a metric."""
        return await self.trends.get_percentile(user_id, metric_type, percentile, limit)

    async def compare_periods(
        self,
        user_id: UUID,
        metric_type: str,
        current_days: int = 7,
        previous_days: int = 7,
    ) -> dict:
        """Compare metric performance between two periods."""
        return await self.trends.compare_periods(
            user_id, metric_type, current_days, previous_days
        )

    # ──────────────────────────────────────────────────────────────────────────────
    # Aggregation API (delegates to AggregationService)
    # ──────────────────────────────────────────────────────────────────────────────

    async def get_productivity(self, user_id: UUID) -> dict:
        """Get productivity domain metrics (learning-focused)."""
        return await self.aggregation.get_learning_metrics(user_id)

    async def get_habit_metrics(self, user_id: UUID) -> dict:
        """Get habit domain metrics."""
        return await self.aggregation.get_habit_metrics(user_id)

    async def get_health_metrics(self, user_id: UUID) -> dict:
        """Get health domain metrics."""
        return await self.aggregation.get_health_metrics(user_id)

    async def get_knowledge_metrics(self, user_id: UUID) -> dict:
        """Get knowledge domain metrics."""
        return await self.aggregation.get_knowledge_metrics(user_id)

    async def get_cross_domain_score(self, user_id: UUID) -> int:
        """Compute overall productivity score (0-100)."""
        return await self.aggregation.compute_cross_domain_score(user_id)

    async def get_overview(self, user_id: UUID) -> dict:
        """Get cross-domain analytics overview with caching."""
        cache_key = f"analytics:overview:{user_id}"

        # Check cache first
        cached_data = await self._get_cached(cache_key)
        if cached_data:
            return cached_data

        # Compute overview via aggregation service
        result = await self.aggregation.get_overview(user_id)

        # Cache the result
        await self._set_cached(cache_key, result)

        return result

    # ──────────────────────────────────────────────────────────────────────────────
    # ClickHouse API (delegates to ClickHouseRepository for historical analysis)
    # ──────────────────────────────────────────────────────────────────────────────

    async def get_behavior_pattern(
        self, user_id: UUID, metric_type: str, days: int = 30
    ) -> dict:
        """Get long-term behavior pattern from ClickHouse."""
        if not self.clickhouse:
            return {"status": "unavailable"}
        return await self.clickhouse.compute_behavior_pattern(
            user_id, metric_type, days
        )

    async def detect_anomalies(
        self,
        user_id: UUID,
        metric_type: str,
        threshold: float = 2.0,
        days: int = 30,
    ) -> dict:
        """Detect anomalies using ClickHouse historical data."""
        if not self.clickhouse:
            return {"anomalies": []}
        return await self.clickhouse.detect_anomalies(
            user_id, metric_type, threshold, days
        )

    async def get_metric_correlation(
        self,
        user_id: UUID,
        metric_type_1: str,
        metric_type_2: str,
        days: int = 30,
    ) -> dict:
        """Get cross-metric correlation from ClickHouse."""
        if not self.clickhouse:
            return {"correlation": 0.0}
        return await self.clickhouse.get_cross_metric_correlation(
            user_id, metric_type_1, metric_type_2, days
        )

    async def archive_metrics_to_clickhouse(
        self, user_id: UUID, date, metrics: dict
    ) -> bool:
        """Archive daily aggregated metrics to ClickHouse."""
        if not self.clickhouse:
            return False
        return await self.clickhouse.archive_daily_metrics(user_id, date, metrics)
