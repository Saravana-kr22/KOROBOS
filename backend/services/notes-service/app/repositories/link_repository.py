"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Data access layer for NoteLink operations — wiki-links, backlinks, graph edges.
"""

from uuid import UUID

from app.models.link_model import NoteLink
from app.models.note_model import Note
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class LinkRepository:
    """Repository for NoteLink CRUD and backlink queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def link_exists(self, source_id: UUID, target_id: UUID) -> bool:
        result = await self.session.execute(
            select(NoteLink).where(
                NoteLink.source_note_id == source_id,
                NoteLink.target_note_id == target_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_link(self, source_id: UUID, target_id: UUID) -> NoteLink:
        """Create a link or return the existing one (idempotent)."""
        existing = await self.session.execute(
            select(NoteLink).where(
                NoteLink.source_note_id == source_id,
                NoteLink.target_note_id == target_id,
            )
        )
        link = existing.scalar_one_or_none()
        if link is not None:
            return link
        link = NoteLink(source_note_id=source_id, target_note_id=target_id)
        self.session.add(link)
        await self.session.flush()
        return link

    async def get_backlinks(self, note_id: UUID) -> list[Note]:
        """Return all notes that link TO note_id (inbound links)."""
        result = await self.session.execute(
            select(Note)
            .join(NoteLink, NoteLink.source_note_id == Note.id)
            .where(NoteLink.target_note_id == note_id)
            .order_by(Note.created_at.desc())
        )
        return list(result.scalars().all())
