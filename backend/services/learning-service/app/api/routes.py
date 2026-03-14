"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID

from app.schemas.schema import (
    LearningSessionCreate,
    LearningSessionListResponse,
    LearningSessionResponse,
    LearningStatsResponse,
)
from app.services.service_logic import LearningService
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    return UUID(x_user_id)


@router.post(
    "/sessions",
    response_model=LearningSessionResponse,
    status_code=201,
    tags=["Learning"],
)
async def create_session(
    data: LearningSessionCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    svc = LearningService(session)
    learning_session = await svc.log_session(user_id, data)
    await session.commit()
    return learning_session


@router.get("/sessions", response_model=LearningSessionListResponse, tags=["Learning"])
async def list_sessions(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    svc = LearningService(session)
    sessions, total = await svc.list_sessions(user_id, offset=offset, limit=limit)
    return {"sessions": sessions, "total": total}


@router.get(
    "/sessions/{session_id}",
    response_model=LearningSessionResponse,
    tags=["Learning"],
)
async def get_session(
    session_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    svc = LearningService(session)
    learning_session = await svc.get_session(session_id)
    if not learning_session or learning_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Learning session not found")
    return learning_session


@router.get("/stats", response_model=LearningStatsResponse, tags=["Learning"])
async def get_stats(
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    svc = LearningService(session)
    return await svc.get_stats(user_id)


@router.delete("/sessions/{session_id}", status_code=204, tags=["Learning"])
async def delete_session(
    session_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    svc = LearningService(session)
    learning_session = await svc.get_session(session_id)
    if not learning_session or learning_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Learning session not found")
    await svc.delete_session(learning_session)
    await session.commit()


@router.get("/")
async def root():
    return {"message": "Learning Service is running"}
