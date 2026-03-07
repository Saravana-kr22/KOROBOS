"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Habit Service API routes — full CRUD for habits and completion logging.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schema import (
    HabitCreate,
    HabitUpdate,
    HabitResponse,
    HabitListResponse,
    HabitCompleteRequest,
    HabitCompleteResponse,
)
from app.services.service_logic import HabitService

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header (injected by gateway)."""
    return UUID(x_user_id)


# ── CRUD Endpoints ────────────────────────────────────────────────────────


@router.post("/habits", response_model=HabitResponse, status_code=201, tags=["Habits"])
async def create_habit(
    data: HabitCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new habit."""
    svc = HabitService(session)
    habit = await svc.create_habit(user_id, data)
    await session.commit()
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


# ── Completion Endpoints ──────────────────────────────────────────────────


@router.post(
    "/habits/{habit_id}/complete",
    response_model=HabitCompleteResponse,
    tags=["Habits"],
)
async def complete_habit(
    habit_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Mark a habit as completed for today and return the current streak."""
    svc = HabitService(session)
    habit = await svc.get_habit(habit_id)
    if not habit or habit.user_id != user_id:
        raise HTTPException(status_code=404, detail="Habit not found")
    completed, streak = await svc.complete_habit(habit_id)
    await session.commit()
    return {"habit_id": habit_id, "completed": completed, "streak": streak}


@router.get("/", tags=["Habits"])
async def root():
    return {"service": "habit-service", "status": "running"}
