"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

import json
from datetime import date
from typing import Optional
from uuid import UUID

from app.api.rate_limit import check_log_rate_limit
from app.schemas.schema import (
    DailyStatsResponse,
    HealthLogListResponse,
    HealthLogResponse,
    HealthStatsResponse,
    MealLogCreate,
    WorkoutLogCreate,
)
from app.services.service_logic import HealthService
from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    return UUID(x_user_id)


@router.post(
    "/meals",
    response_model=HealthLogResponse,
    status_code=201,
    tags=["Health"],
    dependencies=[Depends(check_log_rate_limit)],
)
async def log_meal(
    data: MealLogCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    from app.main import MEALS_LOGGED

    svc = HealthService(session)
    log = await svc.log_meal(user_id, data)
    await session.commit()
    MEALS_LOGGED.labels(service="health-service").inc()
    return log


@router.post(
    "/workouts",
    response_model=HealthLogResponse,
    status_code=201,
    tags=["Health"],
    dependencies=[Depends(check_log_rate_limit)],
)
async def log_workout(
    data: WorkoutLogCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    from app.main import WORKOUTS_LOGGED

    svc = HealthService(session)
    log = await svc.log_workout(user_id, data)
    await session.commit()
    WORKOUTS_LOGGED.labels(service="health-service").inc()
    return log


@router.get("/logs", response_model=HealthLogListResponse, tags=["Health"])
async def list_logs(
    log_type: Optional[str] = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    svc = HealthService(session)
    logs, total = await svc.list_logs(
        user_id,
        log_type=log_type,
        offset=offset,
        limit=limit,
    )
    return {"logs": logs, "total": total}


@router.get("/stats", response_model=HealthStatsResponse, tags=["Health"])
async def get_stats(
    request: Request,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    redis = getattr(request.app.state, "redis", None)
    cache_key = f"cache:health:stats:{user_id}"

    # Try to load from Redis cache
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # cache miss, proceed

    # Compute stats
    svc = HealthService(session)
    result = await svc.get_stats(user_id)

    # Cache the result (2-minute TTL)
    if redis:
        try:
            await redis.set(cache_key, json.dumps(result, default=str), ex=120)
        except Exception:
            pass  # never block on cache failure

    return result


@router.get("/daily", response_model=DailyStatsResponse, tags=["Health"])
async def get_daily_stats(
    request: Request,
    date_param: Optional[str] = Query(None, alias="date"),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get daily calorie stats (consumed, burned, net) for a given date."""
    date_: Optional[date] = None
    if date_param:
        try:
            date_ = date.fromisoformat(date_param)
        except ValueError:
            date_ = None  # defaults to today

    redis = getattr(request.app.state, "redis", None)
    cache_key = f"cache:health:daily:{user_id}:{date_ or 'today'}"

    # Try to load from Redis cache
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # cache miss, proceed

    # Compute daily stats
    svc = HealthService(session)
    result = await svc.get_daily_stats(user_id, date_)

    # Cache the result (2-minute TTL)
    if redis:
        try:
            await redis.set(cache_key, json.dumps(result, default=str), ex=120)
        except Exception:
            pass  # never block on cache failure

    return result


@router.delete("/logs/{log_id}", status_code=204, tags=["Health"])
async def delete_log(
    log_id: UUID,
    request: Request,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a health log."""
    svc = HealthService(session)
    result = await svc.delete_log(user_id, log_id)
    if result is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Log not found")
    await session.commit()

    # Invalidate cache
    redis = getattr(request.app.state, "redis", None)
    if redis:
        try:
            await redis.delete(f"cache:health:stats:{user_id}")
            await redis.delete(f"cache:health:daily:{user_id}:*")
        except Exception:
            pass


@router.get("/")
async def root():
    return {"message": "Health Service is running"}
