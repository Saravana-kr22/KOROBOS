"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service business logic — aggregation orchestration and caching.
"""

import asyncio
from datetime import date, timedelta
from uuid import UUID

import redis.asyncio as aioredis
from app.config.settings import DashboardSettings
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard_schema import DailyMetrics, OverviewResponse, WeeklyResponse
from app.services.aggregation_engine import AggregationEngine
from app.services.metric_engine import MetricEngine
from sqlalchemy.ext.asyncio import AsyncSession


def _get_cache_metrics():
    """Lazy import to avoid circular dependency with main.py."""
    from app.main import CACHE_HITS, CACHE_MISSES

    return CACHE_HITS, CACHE_MISSES


class DashboardService:
    """
    Orchestrates dashboard aggregation, caching, and persistence.

    Calls AggregationEngine to fetch data, MetricEngine to compute scores,
    and Repository to persist/retrieve snapshots. Manages Redis caching.
    """

    def __init__(
        self,
        session: AsyncSession,
        settings: DashboardSettings,
        redis_client: aioredis.Redis | None = None,
    ):
        self.session = session
        self.settings = settings
        self.redis = redis_client
        self.repo = DashboardRepository(session)
        self.engine = AggregationEngine(settings)
        self.metrics = MetricEngine()

    async def get_daily(
        self,
        user_id: UUID,
        headers: dict,
        snapshot_date: date | None = None,
    ) -> DailyMetrics:
        """
        Get daily metrics for a specific date.

        Flow:
        1. Try Redis cache
        2. If miss, call aggregation engine (concurrent)
        3. Compute scores via MetricEngine
        4. Upsert daily_snapshot in DB
        5. Cache result
        6. Return DailyMetrics
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        cache_key = f"cache:dashboard:daily:{user_id}:{snapshot_date.isoformat()}"

        # Try cache first
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    cache_hits, _ = _get_cache_metrics()
                    cache_hits.labels(endpoint="get_daily").inc()
                    return DailyMetrics.model_validate_json(cached)
                else:
                    _, cache_misses = _get_cache_metrics()
                    cache_misses.labels(endpoint="get_daily").inc()
            except Exception:
                _, cache_misses = _get_cache_metrics()
                cache_misses.labels(endpoint="get_daily").inc()
        else:
            _, cache_misses = _get_cache_metrics()
            cache_misses.labels(endpoint="get_daily").inc()

        # Fetch from all services concurrently
        (
            habit_data,
            health_data,
            learning_data,
            notes_data,
            db_data,
        ) = await asyncio.gather(
            self.engine.get_habit_data(str(user_id), headers),
            self.engine.get_health_data(str(user_id), headers),
            self.engine.get_learning_data(str(user_id), headers),
            self.engine.get_notes_data(str(user_id), headers),
            self.engine.get_database_data(str(user_id), headers),
        )

        # Compute domain scores
        habit_score = self.metrics.habit_score(
            habit_data.get("habits_completed", 0),
            habit_data.get("total_habits", 0),
        )
        learning_score = self.metrics.learning_score(
            learning_data.get("learning_minutes", 0)
        )
        health_score = self.metrics.health_score(health_data.get("net_calories", 0))

        # Compute overall productivity score
        productivity_score = self.metrics.compute_productivity_score(
            habit_score, learning_score, health_score
        )

        # Upsert snapshot to DB
        await self.repo.upsert_snapshot(
            user_id=user_id,
            snapshot_date=snapshot_date,
            habits_completed=habit_data.get("habits_completed", 0),
            total_habits=habit_data.get("total_habits", 0),
            learning_minutes=learning_data.get("learning_minutes", 0),
            calories_consumed=health_data.get("calories_consumed", 0),
            calories_burned=health_data.get("calories_burned", 0),
            net_calories=health_data.get("net_calories", 0),
            productivity_score=productivity_score,
            notes_created_today=notes_data.get("notes_created_today", 0),
            records_created_today=db_data.get("records_created_today", 0),
            current_streak=habit_data.get("current_streak", 0),
        )
        await self.session.commit()

        # Build response
        result = DailyMetrics(
            date=snapshot_date.isoformat(),
            habits_completed=habit_data.get("habits_completed", 0),
            total_habits=habit_data.get("total_habits", 0),
            learning_minutes=learning_data.get("learning_minutes", 0),
            calories_consumed=health_data.get("calories_consumed", 0),
            calories_burned=health_data.get("calories_burned", 0),
            net_calories=health_data.get("net_calories", 0),
            productivity_score=productivity_score,
            notes_created_today=notes_data.get("notes_created_today", 0),
            records_created_today=db_data.get("records_created_today", 0),
            current_streak=habit_data.get("current_streak", 0),
        )

        # Cache result (5-minute TTL)
        if self.redis:
            try:
                await self.redis.set(cache_key, result.model_dump_json(), ex=300)
            except Exception:
                pass

        return result

    async def get_overview(
        self,
        user_id: UUID,
        headers: dict,
    ) -> OverviewResponse:
        """
        Get simplified overview (summary card data).

        Delegates to get_daily(today) and returns simplified response.
        """
        cache_key = f"cache:dashboard:overview:{user_id}"

        # Try cache first
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    cache_hits, _ = _get_cache_metrics()
                    cache_hits.labels(endpoint="get_overview").inc()
                    return OverviewResponse.model_validate_json(cached)
                else:
                    _, cache_misses = _get_cache_metrics()
                    cache_misses.labels(endpoint="get_overview").inc()
            except Exception:
                _, cache_misses = _get_cache_metrics()
                cache_misses.labels(endpoint="get_overview").inc()
        else:
            _, cache_misses = _get_cache_metrics()
            cache_misses.labels(endpoint="get_overview").inc()

        daily = await self.get_daily(user_id, headers)

        result = OverviewResponse(
            date=daily.date,
            habits_completed=daily.habits_completed,
            learning_minutes=daily.learning_minutes,
            calories_balance=daily.net_calories,
            productivity_score=daily.productivity_score,
        )

        # Cache result (5-minute TTL)
        if self.redis:
            try:
                await self.redis.set(cache_key, result.model_dump_json(), ex=300)
            except Exception:
                pass

        return result

    async def get_weekly(
        self,
        user_id: UUID,
        headers: dict,
    ) -> WeeklyResponse:
        """
        Get weekly trends.

        Fetch last 7 daily_snapshots, refresh today via get_daily,
        compute aggregates (average productivity score, total learning, etc).
        """
        cache_key = f"cache:dashboard:weekly:{user_id}:{date.today().isocalendar()[1]}"

        # Try cache first
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    cache_hits, _ = _get_cache_metrics()
                    cache_hits.labels(endpoint="get_weekly").inc()
                    return WeeklyResponse.model_validate_json(cached)
                else:
                    _, cache_misses = _get_cache_metrics()
                    cache_misses.labels(endpoint="get_weekly").inc()
            except Exception:
                _, cache_misses = _get_cache_metrics()
                cache_misses.labels(endpoint="get_weekly").inc()
        else:
            _, cache_misses = _get_cache_metrics()
            cache_misses.labels(endpoint="get_weekly").inc()

        today = date.today()
        week_ago = today - timedelta(days=6)

        # Fetch historical snapshots (last 6 days)
        snapshots = await self.repo.get_weekly_snapshots(
            user_id, week_ago, today - timedelta(days=1)
        )

        # Refresh today's data
        today_metrics = await self.get_daily(user_id, headers, today)

        # Build daily metrics list (7 days)
        days = []
        for i in range(7):
            current_date = week_ago + timedelta(days=i)
            if current_date == today:
                days.append(today_metrics)
            else:
                snap = next(
                    (
                        s
                        for s in snapshots
                        if s.snapshot_date == current_date.isoformat()
                    ),
                    None,
                )
                if snap:
                    days.append(
                        DailyMetrics(
                            date=snap.snapshot_date,
                            habits_completed=snap.habits_completed,
                            total_habits=snap.total_habits,
                            learning_minutes=snap.learning_minutes,
                            calories_consumed=snap.calories_consumed,
                            calories_burned=snap.calories_burned,
                            net_calories=snap.net_calories,
                            productivity_score=snap.productivity_score,
                            notes_created_today=snap.notes_created_today,
                            records_created_today=snap.records_created_today,
                            current_streak=snap.current_streak,
                        )
                    )

        # Compute aggregates
        avg_productivity = (
            sum(d.productivity_score for d in days) / len(days) if days else 0.0
        )
        total_learning = sum(d.learning_minutes for d in days)
        avg_habits = sum(d.habits_completed for d in days) / len(days) if days else 0.0
        consistency = self.metrics.consistency_score(
            [d.productivity_score for d in days]
        )

        result = WeeklyResponse(
            week_start=week_ago.isoformat(),
            week_end=today.isoformat(),
            days=days,
            avg_productivity_score=round(avg_productivity, 1),
            total_learning_minutes=total_learning,
            avg_habits_completed=round(avg_habits, 1),
            consistency_score=round(consistency, 1),
        )

        # Cache result (5-minute TTL)
        if self.redis:
            try:
                await self.redis.set(cache_key, result.model_dump_json(), ex=300)
            except Exception:
                pass

        return result
