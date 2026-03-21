"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Timer Service — manages active learning session lifecycle.
"""

from uuid import UUID

from app.events.learning_events import (
    LearningSessionCompletedEvent,
    LearningSessionStartedEvent,
)
from app.models.session_model import LearningSession
from app.repositories.session_repository import LearningRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.learning_schema import (
    SessionPauseRequest,
    SessionResumeRequest,
    SessionStartRequest,
    SessionStopRequest,
)
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.messaging.producer import publish_event


class TimerService:
    def __init__(self, session: AsyncSession):
        self.repo = LearningRepository(session)
        self.topic_repo = TopicRepository(session)

    async def start_session(
        self, user_id: UUID, data: SessionStartRequest
    ) -> LearningSession:
        """Start a new active timer session.

        Raises 409 if the user already has an active/paused session.
        """
        existing = await self.repo.get_active_session(user_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "SESSION_ALREADY_ACTIVE",
                    "message": "A session is already active. Stop or pause it first.",
                    "session_id": str(existing.id),
                },
            )

        if data.topic_id is not None:
            topic = await self.topic_repo.get_by_id(data.topic_id)
            if not topic or topic.user_id != user_id:
                raise HTTPException(status_code=404, detail="Topic not found")

        session = await self.repo.create_active_session(
            user_id=user_id,
            topic=data.topic,
            topic_id=data.topic_id,
            notes=data.notes,
        )

        try:
            event = LearningSessionStartedEvent(
                payload={
                    "session_id": str(session.id),
                    "user_id": str(user_id),
                    "topic": data.topic,
                    "start_time": session.start_time.isoformat()
                    if session.start_time
                    else None,
                }
            )
            await publish_event(event, key=str(user_id))
        except Exception:
            pass  # Event failure must not block the timer

        return session

    async def stop_session(
        self, user_id: UUID, data: SessionStopRequest
    ) -> LearningSession:
        """Stop (complete) an active or paused session."""
        session = await self.repo.get_by_id(data.session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.status not in ("active", "paused"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "SESSION_NOT_ACTIVE",
                    "message": (
                        f"Session status is '{session.status}', not active or paused."
                    ),
                },
            )

        session = await self.repo.stop_session(session, notes=data.notes)

        try:
            event = LearningSessionCompletedEvent(
                payload={
                    "session_id": str(session.id),
                    "user_id": str(user_id),
                    "topic": session.topic,
                    "duration": session.duration,
                    "start_time": session.start_time.isoformat()
                    if session.start_time
                    else None,
                    "end_time": session.end_time.isoformat()
                    if session.end_time
                    else None,
                }
            )
            await publish_event(event, key=str(user_id))
        except Exception:
            pass

        return session

    async def pause_session(
        self, user_id: UUID, data: SessionPauseRequest
    ) -> LearningSession:
        """Pause an active session."""
        session = await self.repo.get_by_id(data.session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.status != "active":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "SESSION_NOT_ACTIVE",
                    "message": "Only active sessions can be paused.",
                },
            )
        return await self.repo.pause_session(session)

    async def resume_session(
        self, user_id: UUID, data: SessionResumeRequest
    ) -> LearningSession:
        """Resume a paused session."""
        session = await self.repo.get_by_id(data.session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.status != "paused":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "SESSION_NOT_PAUSED",
                    "message": "Only paused sessions can be resumed.",
                },
            )
        return await self.repo.resume_session(session)
