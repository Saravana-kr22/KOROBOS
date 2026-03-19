"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Learning Service API routes — sessions, topics, timer, notes integration.
"""

import json
from uuid import UUID

from app.api.rate_limit import check_session_log_rate_limit
from app.schemas.learning_schema import (
    LearningSessionCreate,
    LearningSessionListResponse,
    LearningSessionResponse,
    LearningStatsResponse,
    LinkNoteRequest,
    SessionNotesResponse,
    SessionPauseRequest,
    SessionResumeRequest,
    SessionStartRequest,
    SessionStopRequest,
    TopicCreate,
    TopicListResponse,
    TopicResponse,
    TopicUpdate,
)
from app.services.analytics_service import AnalyticsService
from app.services.learning_service import LearningService
from app.services.timer_service import TimerService
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header (injected by gateway)."""
    return UUID(x_user_id)


# ===========================================================================
# Topics
# ===========================================================================


@router.post("/topics", response_model=TopicResponse, status_code=201, tags=["Topics"])
async def create_topic(
    data: TopicCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new learning topic."""
    from app.main import SESSIONS_CREATED

    svc = LearningService(session)
    topic = await svc.create_topic(user_id, data)
    await session.commit()
    SESSIONS_CREATED.labels(type="topic").inc()
    return topic


@router.get("/topics", response_model=TopicListResponse, tags=["Topics"])
async def list_topics(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """List all topics for the authenticated user."""
    svc = LearningService(session)
    topics, total = await svc.list_topics(user_id, offset=offset, limit=limit)
    return {"topics": topics, "total": total}


@router.put("/topics/{topic_id}", response_model=TopicResponse, tags=["Topics"])
async def update_topic(
    topic_id: UUID,
    data: TopicUpdate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Update a topic name."""
    svc = LearningService(session)
    topic = await svc.get_topic(topic_id)
    if not topic or topic.user_id != user_id:
        raise HTTPException(status_code=404, detail="Topic not found")
    updated = await svc.update_topic(topic, data)
    await session.commit()
    return updated


@router.delete("/topics/{topic_id}", status_code=204, tags=["Topics"])
async def delete_topic(
    topic_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a topic. Sessions linked to it will have topic_id set to NULL."""
    svc = LearningService(session)
    topic = await svc.get_topic(topic_id)
    if not topic or topic.user_id != user_id:
        raise HTTPException(status_code=404, detail="Topic not found")
    await svc.delete_topic(topic)
    await session.commit()


# ===========================================================================
# Timer Engine
# ===========================================================================


@router.post(
    "/session/start",
    response_model=LearningSessionResponse,
    status_code=201,
    tags=["Timer"],
)
async def start_session(
    data: SessionStartRequest,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Start a live learning timer session.

    Returns 409 if the user already has an active or paused session.
    """
    svc = TimerService(session)
    learning_session = await svc.start_session(user_id, data)
    await session.commit()
    return learning_session


@router.post(
    "/session/stop",
    response_model=LearningSessionResponse,
    tags=["Timer"],
)
async def stop_session(
    data: SessionStopRequest,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Stop (complete) an active or paused session. Computes total duration."""
    from app.main import LEARNING_MINUTES_TOTAL, SESSIONS_CREATED

    svc = TimerService(session)
    learning_session = await svc.stop_session(user_id, data)
    await session.commit()
    SESSIONS_CREATED.labels(type="timer").inc()
    LEARNING_MINUTES_TOTAL.inc(learning_session.duration)
    return learning_session


@router.post(
    "/session/pause",
    response_model=LearningSessionResponse,
    tags=["Timer"],
)
async def pause_session(
    data: SessionPauseRequest,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Pause an active timer session."""
    svc = TimerService(session)
    learning_session = await svc.pause_session(user_id, data)
    await session.commit()
    return learning_session


@router.post(
    "/session/resume",
    response_model=LearningSessionResponse,
    tags=["Timer"],
)
async def resume_session(
    data: SessionResumeRequest,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Resume a paused timer session."""
    svc = TimerService(session)
    learning_session = await svc.resume_session(user_id, data)
    await session.commit()
    return learning_session


# ===========================================================================
# Session CRUD + Manual Log
# ===========================================================================


@router.post(
    "/session/log",
    response_model=LearningSessionResponse,
    status_code=201,
    tags=["Learning"],
    dependencies=[Depends(check_session_log_rate_limit)],
)
async def log_session(
    data: LearningSessionCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Manually log a completed learning session (topic + duration)."""
    from app.main import LEARNING_MINUTES_TOTAL, SESSIONS_CREATED

    svc = LearningService(session)
    learning_session = await svc.log_session(user_id, data)
    await session.commit()
    SESSIONS_CREATED.labels(type="manual").inc()
    LEARNING_MINUTES_TOTAL.inc(data.duration)
    return learning_session


# Keep POST /sessions as the canonical endpoint (backward compat)
@router.post(
    "/sessions",
    response_model=LearningSessionResponse,
    status_code=201,
    tags=["Learning"],
    dependencies=[Depends(check_session_log_rate_limit)],
)
async def create_session(
    data: LearningSessionCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Manually log a completed learning session."""
    from app.main import LEARNING_MINUTES_TOTAL, SESSIONS_CREATED

    svc = LearningService(session)
    learning_session = await svc.log_session(user_id, data)
    await session.commit()
    SESSIONS_CREATED.labels(type="manual").inc()
    LEARNING_MINUTES_TOTAL.inc(data.duration)
    return learning_session


@router.get("/sessions", response_model=LearningSessionListResponse, tags=["Learning"])
async def list_sessions(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """List learning sessions for the authenticated user (paginated)."""
    redis = getattr(request.app.state, "redis", None)
    cache_key = f"cache:learning:sessions:{user_id}:{offset}:{limit}"

    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    svc = LearningService(session)
    sessions, total = await svc.list_sessions(user_id, offset=offset, limit=limit)

    if redis:
        try:
            serialized = [
                LearningSessionResponse.model_validate(s).model_dump(mode="json")
                for s in sessions
            ]
            await redis.set(
                cache_key,
                json.dumps({"sessions": serialized, "total": total}),
                ex=120,
            )
        except Exception:
            pass

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
    """Get a single learning session by ID."""
    svc = LearningService(session)
    learning_session = await svc.get_session(session_id)
    if not learning_session or learning_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Learning session not found")
    return learning_session


@router.delete("/sessions/{session_id}", status_code=204, tags=["Learning"])
async def delete_session(
    session_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a learning session."""
    svc = LearningService(session)
    learning_session = await svc.get_session(session_id)
    if not learning_session or learning_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Learning session not found")
    await svc.delete_session(learning_session)
    await session.commit()


# ===========================================================================
# Analytics
# ===========================================================================


@router.get("/stats", response_model=LearningStatsResponse, tags=["Analytics"])
async def get_stats(
    request: Request,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get enhanced learning analytics for the authenticated user."""
    redis = getattr(request.app.state, "redis", None)
    cache_key = f"cache:learning:stats:{user_id}"

    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    analytics = AnalyticsService(session)
    stats = await analytics.get_stats(user_id)

    if redis:
        try:
            await redis.set(cache_key, json.dumps(stats, default=str), ex=120)
        except Exception:
            pass

    return stats


# ===========================================================================
# Note Linking
# ===========================================================================


@router.post(
    "/sessions/{session_id}/notes",
    status_code=204,
    tags=["Notes Integration"],
)
async def link_note(
    session_id: UUID,
    data: LinkNoteRequest,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Link a note to a learning session."""
    svc = LearningService(session)
    learning_session = await svc.get_session(session_id)
    if not learning_session or learning_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Learning session not found")
    await svc.link_note(session_id, data.note_id)
    await session.commit()


@router.delete(
    "/sessions/{session_id}/notes/{note_id}",
    status_code=204,
    tags=["Notes Integration"],
)
async def unlink_note(
    session_id: UUID,
    note_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Unlink a note from a learning session."""
    svc = LearningService(session)
    learning_session = await svc.get_session(session_id)
    if not learning_session or learning_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Learning session not found")
    await svc.unlink_note(session_id, note_id)
    await session.commit()


@router.get(
    "/sessions/{session_id}/notes",
    response_model=SessionNotesResponse,
    tags=["Notes Integration"],
)
async def get_session_notes(
    session_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get all note IDs linked to a learning session."""
    svc = LearningService(session)
    learning_session = await svc.get_session(session_id)
    if not learning_session or learning_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Learning session not found")
    note_ids = await svc.get_session_notes(session_id)
    return {"session_id": session_id, "note_ids": note_ids}


# ===========================================================================
# Root
# ===========================================================================


@router.get("/", tags=["Learning"])
async def root():
    return {"service": "learning-service", "status": "running"}
