"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Habit Service API routes — full CRUD for habits and completion logging.
"""

import json
from uuid import UUID

from app.api.rate_limit import check_completion_rate_limit
from app.schemas.schema import (
    HabitCompleteResponse,
    HabitCreate,
    HabitListResponse,
    HabitResponse,
    HabitStatsResponse,
    HabitTodayResponse,
    HabitUpdate,
)
from app.services.service_logic import HabitService
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header (injected by gateway)."""
    return UUID(x_user_id)


# -- CRUD Endpoints --


@router.post("/habits", response_model=HabitResponse, status_code=201, tags=["Habits"])
async def create_habit(
    data: HabitCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new habit."""
    from app.main import HABITS_CREATED

    svc = HabitService(session)
    habit = await svc.create_habit(user_id, data)
    await session.commit()
    HABITS_CREATED.labels(service="habit-service").inc()
    return habit


@router.get("/habits", response_model=HabitListResponse, tags=["Habits"])
async def list_habits(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """List all habits for the authenticated user."""
    svc = HabitService(session)
    habits, total = await svc.list_habits(user_id, offset, limit)
    return {"habits": habits, "total": total}


@router.get("/habits/today", response_model=HabitTodayResponse, tags=["Habits"])
async def get_today_habits(
    request: Request,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get today's active daily habits with completion status."""
    redis = getattr(request.app.state, "redis", None)
    cache_key = f"cache:habits:today:{user_id}"

    # Try cache first
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # Cache miss or error — proceed to compute

    svc = HabitService(session)
    habits = await svc.get_today_habits(user_id)
    result = {"habits": habits}

    # Store in cache (2-minute TTL)
    if redis:
        try:
            await redis.set(cache_key, json.dumps(result, default=str), ex=120)
        except Exception:
            pass  # Cache failure — return result anyway

    return result


@router.get("/habits/{habit_id}", response_model=HabitResponse, tags=["Habits"])
async def get_habit(
    habit_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get a single habit by ID."""
    svc = HabitService(session)
    habit = await svc.get_habit(habit_id)
    if not habit or habit.user_id != user_id:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.get(
    "/habits/{habit_id}/stats", response_model=HabitStatsResponse, tags=["Habits"]
)
async def get_habit_stats(
    habit_id: UUID,
    request: Request,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get habit statistics: completion rate, streaks, and weekly consistency."""
    redis = getattr(request.app.state, "redis", None)
    cache_key = f"cache:habits:stats:{habit_id}"

    # Try cache first
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # Cache miss or error — proceed to compute

    svc = HabitService(session)
    habit = await svc.get_habit(habit_id)
    if not habit or habit.user_id != user_id:
        raise HTTPException(status_code=404, detail="Habit not found")
    stats = await svc.get_stats(habit_id)

    # Store in cache (2-minute TTL)
    if redis:
        try:
            await redis.set(cache_key, json.dumps(stats, default=str), ex=120)
        except Exception:
            pass  # Cache failure — return result anyway

    return stats


@router.put("/habits/{habit_id}", response_model=HabitResponse, tags=["Habits"])
async def update_habit(
    habit_id: UUID,
    data: HabitUpdate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Update an existing habit."""
    svc = HabitService(session)
    habit = await svc.get_habit(habit_id)
    if not habit or habit.user_id != user_id:
        raise HTTPException(status_code=404, detail="Habit not found")
    updated = await svc.update_habit(habit, data)
    await session.commit()
    return updated


@router.delete("/habits/{habit_id}", status_code=204, tags=["Habits"])
async def delete_habit(
    habit_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a habit."""
    svc = HabitService(session)
    habit = await svc.get_habit(habit_id)
    if not habit or habit.user_id != user_id:
        raise HTTPException(status_code=404, detail="Habit not found")
    await svc.delete_habit(habit)
    await session.commit()


# -- Completion Endpoints --


@router.post(
    "/habits/{habit_id}/complete",
    response_model=HabitCompleteResponse,
    tags=["Habits"],
    dependencies=[Depends(check_completion_rate_limit)],
)
async def complete_habit(
    habit_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Mark a habit as completed for today and return the current streak."""
    from app.main import HABITS_COMPLETED

    svc = HabitService(session)
    habit = await svc.get_habit(habit_id)
    if not habit or habit.user_id != user_id:
        raise HTTPException(status_code=404, detail="Habit not found")
    completed, streak = await svc.complete_habit(habit_id)
    await session.commit()
    HABITS_COMPLETED.labels(service="habit-service").inc()
    return {"habit_id": habit_id, "completed": completed, "streak": streak}


@router.get("/", tags=["Habits"])
async def root():
    return {"service": "habit-service", "status": "running"}
