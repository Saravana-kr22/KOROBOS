"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Business logic layer for the Notes Service.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Note
from app.repositories.repository import NotesRepository
from app.schemas.schema import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import send_event

logger = get_logger("notes-service.logic")


class NotesService:
    """Core business logic for Notes Service."""

    def __init__(self, session: AsyncSession):
        self.repo = NotesRepository(session)

    async def create_note(self, user_id: UUID, data: NoteCreate) -> Note:
        """Create a note and publish the note.created event."""
        note = await self.repo.create(
            user_id=user_id,
            title=data.title,
            content_md=data.content_md,
        )

        # Set tags if provided
        if data.tags:
            await self.repo.set_note_tags(note.id, data.tags)

        # Publish event
        try:
            await send_event(
                topic="note.created",
                value={
                    "event": "note.created",
                    "payload": {
                        "note_id": str(note.id),
                        "user_id": str(user_id),
                        "title": note.title,
                    },
                },
                key=str(user_id),
            )
        except Exception as exc:
            logger.warning(f"Failed to publish note.created event: {exc}")

        return note

    async def get_note(self, note_id: UUID) -> Optional[Note]:
        """Retrieve a note by ID."""
        return await self.repo.get_by_id(note_id)

    async def list_notes(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> tuple[list[Note], int]:
        """List notes for a user with pagination."""
        return await self.repo.list_by_user(user_id, offset, limit)

    async def update_note(self, note: Note, data: NoteUpdate) -> Note:
        """Update a note and publish the note.updated event."""
        updates = data.model_dump(exclude_unset=True, exclude={"tags"})
        note = await self.repo.update(note, **updates)

        if data.tags is not None:
            await self.repo.set_note_tags(note.id, data.tags)

        try:
            await send_event(
                topic="note.updated",
                value={
                    "event": "note.updated",
                    "payload": {
                        "note_id": str(note.id),
                        "user_id": str(note.user_id),
                    },
                },
                key=str(note.user_id),
            )
        except Exception as exc:
            logger.warning(f"Failed to publish note.updated event: {exc}")

        return note

    async def delete_note(self, note: Note) -> None:
        """Delete a note."""
        await self.repo.delete(note)

    async def link_notes(self, source_id: UUID, target_id: UUID):
        """Create a link between two notes and publish event."""
        link = await self.repo.create_link(source_id, target_id)

        try:
            await send_event(
                topic="note.link.created",
                value={
                    "event": "note.link.created",
                    "payload": {
                        "source_note_id": str(source_id),
                        "target_note_id": str(target_id),
                    },
                },
            )
        except Exception as exc:
            logger.warning(f"Failed to publish note.link.created event: {exc}")

        return link
