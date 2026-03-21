"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Session repository for the Learning Service — CRUD, timer, notes, analytics.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.models.session_model import LearningSession, SessionNote
from sqlalchemy import Date as SADate
from sqlalchemy import cast, delete, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LearningRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # Manual session log
    # ------------------------------------------------------------------

    async def create(
        self,
        user_id: UUID,
        topic: str,
        duration: int,
        topic_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        status: str = "completed",
    ) -> LearningSession:
        obj = LearningSession(
            user_id=user_id,
            topic=topic,
            topic_id=topic_id,
            duration=duration,
            notes=notes,
            status=status,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_id(self, session_id: UUID) -> Optional[LearningSession]:
        result = await self.session.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[LearningSession], int]:
        count_q = (
            select(func.count())
            .select_from(LearningSession)
            .where(LearningSession.user_id == user_id)
        )
        total = (await self.session.execute(count_q)).scalar_one()
        q = (
            select(LearningSession)
            .where(LearningSession.user_id == user_id)
            .order_by(LearningSession.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def delete(self, obj: LearningSession) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    # ------------------------------------------------------------------
    # Timer operations
    # ------------------------------------------------------------------

    async def create_active_session(
        self,
        user_id: UUID,
        topic: str,
        topic_id: Optional[UUID] = None,
        notes: Optional[str] = None,
    ) -> LearningSession:
        """Create a new session with status=active and record start_time."""
        now = _utcnow()
        obj = LearningSession(
            user_id=user_id,
            topic=topic,
            topic_id=topic_id,
            duration=0,
            notes=notes,
            status="active",
            start_time=now,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_active_session(self, user_id: UUID) -> Optional[LearningSession]:
        """Return the currently active (or paused) session for a user, if any."""
        result = await self.session.execute(
            select(LearningSession).where(
                LearningSession.user_id == user_id,
                LearningSession.status.in_(["active", "paused"]),
            )
        )
        return result.scalar_one_or_none()

    async def stop_session(
        self, session: LearningSession, notes: Optional[str] = None
    ) -> LearningSession:
        """Complete a session: record end_time and compute total duration."""
        now = _utcnow()
        session.end_time = now
        session.status = "completed"
        if notes is not None:
            session.notes = notes
        # Duration = elapsed time in minutes since start, minimum 1
        if session.start_time:
            elapsed = (now - session.start_time).total_seconds() / 60
            # Add to any already-accumulated duration (from pause cycles)
            session.duration = max(1, session.duration + int(elapsed))
        await self.session.flush()
        return session

    async def pause_session(self, session: LearningSession) -> LearningSession:
        """Pause an active session: accumulate elapsed time, mark paused."""
        now = _utcnow()
        if session.start_time and session.status == "active":
            elapsed = (now - session.start_time).total_seconds() / 60
            session.duration = session.duration + int(elapsed)
            # Reset start_time; will be set again on resume
            session.start_time = None
        session.status = "paused"
        await self.session.flush()
        return session

    async def resume_session(self, session: LearningSession) -> LearningSession:
        """Resume a paused session: record new start_time."""
        session.start_time = _utcnow()
        session.status = "active"
        await self.session.flush()
        return session

    # ------------------------------------------------------------------
    # Note linking
    # ------------------------------------------------------------------

    async def link_note(self, session_id: UUID, note_id: UUID) -> None:
        existing = await self.session.execute(
            select(SessionNote).where(
                SessionNote.session_id == session_id,
                SessionNote.note_id == note_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            self.session.add(SessionNote(session_id=session_id, note_id=note_id))
            await self.session.flush()

    async def unlink_note(self, session_id: UUID, note_id: UUID) -> None:
        await self.session.execute(
            delete(SessionNote).where(
                SessionNote.session_id == session_id,
                SessionNote.note_id == note_id,
            )
        )
        await self.session.flush()

    async def get_session_note_ids(self, session_id: UUID) -> list[UUID]:
        result = await self.session.execute(
            select(SessionNote.note_id).where(SessionNote.session_id == session_id)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    async def get_stats(self, user_id: UUID) -> dict:
        """Return enhanced learning statistics for a user."""
        now = _utcnow()
        today = now.date()
        week_ago = now - timedelta(days=7)

        # Basic aggregates
        total_q = (
            select(func.count())
            .select_from(LearningSession)
            .where(
                LearningSession.user_id == user_id,
                LearningSession.status == "completed",
            )
        )
        minutes_q = select(func.coalesce(func.sum(LearningSession.duration), 0)).where(
            LearningSession.user_id == user_id,
            LearningSession.status == "completed",
        )
        topics_q = select(distinct(LearningSession.topic)).where(
            LearningSession.user_id == user_id,
            LearningSession.status == "completed",
        )

        # Sessions today
        today_q = (
            select(func.count())
            .select_from(LearningSession)
            .where(
                LearningSession.user_id == user_id,
                LearningSession.status == "completed",
                cast(LearningSession.created_at, SADate) == today,
            )
        )

        # Weekly minutes
        weekly_q = select(func.coalesce(func.sum(LearningSession.duration), 0)).where(
            LearningSession.user_id == user_id,
            LearningSession.status == "completed",
            LearningSession.created_at >= week_ago,
        )

        # Topic distribution (topic → total minutes)
        dist_q = (
            select(
                LearningSession.topic,
                func.sum(LearningSession.duration).label("total"),
            )
            .where(
                LearningSession.user_id == user_id,
                LearningSession.status == "completed",
            )
            .group_by(LearningSession.topic)
        )

        total = (await self.session.execute(total_q)).scalar_one()
        minutes = (await self.session.execute(minutes_q)).scalar_one()
        topics = list((await self.session.execute(topics_q)).scalars().all())
        sessions_today = (await self.session.execute(today_q)).scalar_one()
        weekly_minutes = (await self.session.execute(weekly_q)).scalar_one()
        dist_rows = (await self.session.execute(dist_q)).all()
        topic_distribution = {row.topic: int(row.total) for row in dist_rows}

        # Streak: count consecutive days ending today with ≥1 completed session
        streak = await self._calculate_streak(user_id, today)

        return {
            "total_sessions": total,
            "total_minutes": int(minutes),
            "topics": topics,
            "sessions_today": sessions_today,
            "current_streak": streak,
            "weekly_minutes": int(weekly_minutes),
            "topic_distribution": topic_distribution,
        }

    async def _calculate_streak(self, user_id: UUID, today) -> int:
        """Count consecutive days (ending today) that have ≥1 completed session."""
        days_q = (
            select(cast(LearningSession.created_at, SADate).label("day"))
            .where(
                LearningSession.user_id == user_id,
                LearningSession.status == "completed",
            )
            .distinct()
            .order_by(cast(LearningSession.created_at, SADate).desc())
        )
        result = await self.session.execute(days_q)
        days = [row.day for row in result.all()]

        if not days or days[0] != today:
            # No session today — check if yesterday had one (still counts)
            yesterday = today - timedelta(days=1)
            if not days or days[0] != yesterday:
                return 0
            days_to_check = days
            expected = yesterday  # streak starts from yesterday, not today
        else:
            days_to_check = days
            expected = today

        streak = 0
        for day in days_to_check:
            if day == expected:
                streak += 1
                expected = expected - timedelta(days=1)
            elif day < expected:
                break
        return streak
