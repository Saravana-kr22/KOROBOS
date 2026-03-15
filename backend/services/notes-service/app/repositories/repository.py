"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Data access layer for the Notes Service.
"""

from typing import Optional
from uuid import UUID

from app.models.model import Note, NoteLink, NoteTag, Tag
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class NotesRepository:
    """Repository for Note CRUD operations against PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, title: str, content_md: str) -> Note:
        """Create a new note."""
        note = Note(user_id=user_id, title=title, content_md=content_md)
        self.session.add(note)
        await self.session.flush()
        return note

    async def get_by_id(self, note_id: UUID) -> Optional[Note]:
        """Retrieve a single note by ID."""
        result = await self.session.execute(select(Note).where(Note.id == note_id))
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> tuple[list[Note], int]:
        """List notes for a user with pagination."""
        # Count
        count_q = select(func.count()).select_from(Note).where(Note.user_id == user_id)
        total = (await self.session.execute(count_q)).scalar_one()

        # Fetch
        q = (
            select(Note)
            .where(Note.user_id == user_id)
            .order_by(Note.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def update(self, note: Note, **kwargs) -> Note:
        """Update note fields."""
        for key, value in kwargs.items():
            if value is not None:
                setattr(note, key, value)
        await self.session.flush()
        return note

    async def delete(self, note: Note) -> None:
        """Delete a note."""
        await self.session.delete(note)
        await self.session.flush()

    async def link_exists(self, source_id: UUID, target_id: UUID) -> bool:
        """Return True if a NoteLink from source → target already exists."""
        result = await self.session.execute(
            select(NoteLink).where(
                NoteLink.source_note_id == source_id,
                NoteLink.target_note_id == target_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_link(self, source_id: UUID, target_id: UUID) -> NoteLink:
        """Create a link between two notes, or return the existing one."""
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

    async def get_or_create_tag(self, name: str) -> Tag:
        """Get an existing tag or create a new one."""
        result = await self.session.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = Tag(name=name)
            self.session.add(tag)
            await self.session.flush()
        return tag

    async def set_note_tags(self, note_id: UUID, tag_names: list[str]) -> None:
        """Replace all tags on a note."""
        # Remove existing tags
        existing = await self.session.execute(
            select(NoteTag).where(NoteTag.note_id == note_id)
        )
        for nt in existing.scalars().all():
            await self.session.delete(nt)

        # Add new tags
        for name in tag_names:
            tag = await self.get_or_create_tag(name)
            self.session.add(NoteTag(note_id=note_id, tag_id=tag.id))
        await self.session.flush()

    async def list_note_tag_names(self, note_id: UUID) -> list[str]:
        """Return tag names for a note in stable order."""
        result = await self.session.execute(
            select(Tag.name)
            .join(NoteTag, Tag.id == NoteTag.tag_id)
            .where(NoteTag.note_id == note_id)
            .order_by(Tag.name.asc())
        )
        return list(result.scalars().all())

    async def find_by_title(self, user_id: UUID, title: str) -> Optional[Note]:
        """Find a note by exact title for a given user (wiki-link resolution)."""
        result = await self.session.execute(
            select(Note).where(Note.user_id == user_id, Note.title == title)
        )
        return result.scalar_one_or_none()

    async def get_backlinks(self, note_id: UUID) -> list[Note]:
        """Return all notes that link TO note_id (inbound links)."""
        result = await self.session.execute(
            select(Note)
            .join(NoteLink, NoteLink.source_note_id == Note.id)
            .where(NoteLink.target_note_id == note_id)
            .order_by(Note.created_at.desc())
        )
        return list(result.scalars().all())
