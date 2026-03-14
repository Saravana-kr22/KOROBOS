"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from typing import Optional
from uuid import UUID

from app.schemas.schema import (
    HealthLogListResponse,
    HealthLogResponse,
    HealthStatsResponse,
    MealLogCreate,
    WorkoutLogCreate,
)
from app.services.service_logic import HealthService
from backend.shared.database.connection import get_db_session
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    return UUID(x_user_id)


@router.post(
    "/meals",
    response_model=HealthLogResponse,
    status_code=201,
    tags=["Health"],
)
async def log_meal(
    data: MealLogCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    svc = HealthService(session)
    log = await svc.log_meal(user_id, data)
    await session.commit()
    return log


@router.post(
    "/workouts",
    response_model=HealthLogResponse,
    status_code=201,
    tags=["Health"],
)
async def log_workout(
    data: WorkoutLogCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    svc = HealthService(session)
    log = await svc.log_workout(user_id, data)
    await session.commit()
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
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    svc = HealthService(session)
    return await svc.get_stats(user_id)


@router.get("/")
async def root():
    return {"message": "Health Service is running"}
