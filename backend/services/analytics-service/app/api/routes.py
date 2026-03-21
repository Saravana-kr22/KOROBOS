"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID

from app.config.settings import AnalyticsSettings
from app.repositories.clickhouse_repository import ClickHouseRepository
from app.services.service_logic import AnalyticsService
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    return UUID(x_user_id)


async def _get_redis():
    """Get Redis client (optional dependency)."""
    try:
        from redis.asyncio import Redis

        redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        await redis.ping()
        return redis
    except Exception:
        return None  # Graceful degradation if Redis unavailable


def _get_clickhouse_repo() -> ClickHouseRepository:
    """Get ClickHouse repository (optional dependency)."""
    try:
        settings = AnalyticsSettings()
        return ClickHouseRepository(
            clickhouse_url=settings.clickhouse_url,
            user=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_database,
        )
    except Exception:
        return None  # Graceful degradation if ClickHouse unavailable


@router.get("/")
async def root():
    return {"message": "Analytics Service is running"}


@router.get("/productivity")
async def get_productivity(
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    redis=Depends(_get_redis),
    ch_repo=Depends(_get_clickhouse_repo),
):
    """Return aggregated productivity, habit consistency, and learning hours."""
    svc = AnalyticsService(session, redis, ch_repo)
    data = await svc.get_productivity(user_id)
    return {"status": "success", "data": data}


@router.get("/habits")
async def get_habit_metrics(
    limit: int = Query(30, ge=1, le=90),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    redis=Depends(_get_redis),
    ch_repo=Depends(_get_clickhouse_repo),
):
    """Return habit completion metrics and trends with pagination."""
    svc = AnalyticsService(session, redis, ch_repo)
    data = await svc.get_trend(user_id, "habit_completion_rate", limit, offset)
    return {"status": "success", "data": data}


@router.get("/learning")
async def get_learning_metrics(
    limit: int = Query(30, ge=1, le=90),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    redis=Depends(_get_redis),
    ch_repo=Depends(_get_clickhouse_repo),
):
    """Return learning hours trend data with pagination."""
    svc = AnalyticsService(session, redis, ch_repo)
    data = await svc.get_trend(user_id, "learning_hours", limit, offset)
    return {"status": "success", "data": data}


@router.get("/overview")
async def get_overview(
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    redis=Depends(_get_redis),
    ch_repo=Depends(_get_clickhouse_repo),
):
    """Return cross-domain analytics overview with caching."""
    svc = AnalyticsService(session, redis, ch_repo)
    data = await svc.get_overview(user_id)

    return {
        "status": "success",
        "data": data,
    }


@router.get("/health")
async def get_health_analytics(
    limit: int = Query(30, ge=1, le=90),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    redis=Depends(_get_redis),
    ch_repo=Depends(_get_clickhouse_repo),
):
    """Return health metrics and trends with pagination."""
    svc = AnalyticsService(session, redis, ch_repo)
    current = await svc.get_health_metrics(user_id)
    intake_trend = await svc.get_trend(user_id, "calorie_intake", limit, offset)
    burned_trend = await svc.get_trend(user_id, "calorie_burned", limit, offset)

    return {
        "status": "success",
        "data": {
            "current": current,
            "intake_trend": intake_trend,
            "burned_trend": burned_trend,
        },
    }


@router.get("/trends")
async def get_trends(
    period: str = Query("7d", regex="^(7d|30d|90d)$"),
    limit: int = Query(30, ge=1, le=90),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    redis=Depends(_get_redis),
    ch_repo=Depends(_get_clickhouse_repo),
):
    """Return trends for all metrics across specified period with pagination."""
    svc = AnalyticsService(session, redis, ch_repo)

    return {
        "status": "success",
        "data": {
            "habits": await svc.get_trend(
                user_id, "habit_completion_rate", limit, offset
            ),
            "learning": await svc.get_trend(user_id, "learning_hours", limit, offset),
            "health_intake": await svc.get_trend(
                user_id, "calorie_intake", limit, offset
            ),
            "health_burned": await svc.get_trend(
                user_id, "calorie_burned", limit, offset
            ),
            "notes": await svc.get_trend(user_id, "notes_created", limit, offset),
            "records": await svc.get_trend(user_id, "records_created", limit, offset),
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# ClickHouse OLAP Analytics — Long-term behavioral insights
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/patterns/{metric_type}")
async def get_behavior_pattern(
    metric_type: str,
    days: int = Query(30, ge=7, le=365),
    user_id: UUID = Depends(_get_user_id),
    ch_repo=Depends(_get_clickhouse_repo),
):
    """
    Get long-term behavior pattern for a metric.

    Returns: mean, std_dev, consistency_score, trend_direction, anomaly count.
    """
    if not ch_repo:
        return {
            "status": "unavailable",
            "message": "ClickHouse analytics not available",
        }

    pattern = await ch_repo.compute_behavior_pattern(user_id, metric_type, days)
    return {
        "status": "success",
        "data": pattern,
    }


@router.get("/anomalies/{metric_type}")
async def detect_anomalies(
    metric_type: str,
    days: int = Query(30, ge=7, le=365),
    threshold: float = Query(2.0, ge=1.0, le=5.0),
    user_id: UUID = Depends(_get_user_id),
    ch_repo=Depends(_get_clickhouse_repo),
):
    """
    Detect anomalies in metric data using statistical analysis.

    threshold: Number of standard deviations from mean to flag as anomaly.
    """
    if not ch_repo:
        return {
            "status": "unavailable",
            "message": "ClickHouse analytics not available",
        }

    anomalies = await ch_repo.detect_anomalies(user_id, metric_type, threshold, days)
    return {
        "status": "success",
        "data": anomalies,
    }


@router.get("/correlation")
async def get_metric_correlation(
    metric1: str = Query(..., description="First metric type"),
    metric2: str = Query(..., description="Second metric type"),
    days: int = Query(30, ge=7, le=365),
    user_id: UUID = Depends(_get_user_id),
    ch_repo=Depends(_get_clickhouse_repo),
):
    """
    Compute correlation between two metrics (Pearson correlation coefficient).

    Returns correlation in range [-1, 1] where:
    - 1 = perfect positive correlation
    - 0 = no correlation
    - -1 = perfect negative correlation
    """
    if not ch_repo:
        return {
            "status": "unavailable",
            "message": "ClickHouse analytics not available",
        }

    correlation = await ch_repo.get_cross_metric_correlation(
        user_id, metric1, metric2, days
    )
    return {
        "status": "success",
        "data": correlation,
    }
