"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID

from app.services.service_logic import AnalyticsService
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    return UUID(x_user_id)


@router.get("/")
async def root():
    return {"message": "Analytics Service is running"}


@router.get("/productivity")
async def get_productivity(
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Return aggregated productivity, habit consistency, and learning hours."""
    svc = AnalyticsService(session)
    data = await svc.get_productivity(user_id)
    return {"status": "success", "data": data}


@router.get("/habit-trends")
async def get_habit_trends(
    limit: int = Query(30, ge=1, le=90),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Return habit consistency trend data for charting."""
    svc = AnalyticsService(session)
    data = await svc.get_trend(user_id, "habit_consistency", limit)
    return {"status": "success", "data": data}


@router.get("/learning-growth")
async def get_learning_growth(
    limit: int = Query(30, ge=1, le=90),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Return learning hours trend data for charting."""
    svc = AnalyticsService(session)
    data = await svc.get_trend(user_id, "learning_hours", limit)
    return {"status": "success", "data": data}
