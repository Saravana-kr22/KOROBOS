"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Business logic layer for the Notes Service.
"""

import json
import logging
from typing import Optional
from uuid import UUID

import nh3
from app.events.notes_events import (
    NoteCreatedEvent,
    NoteDeletedEvent,
    NoteLinkCreatedEvent,
    NoteUpdatedEvent,
)
from app.models.note_model import Note
from app.repositories.link_repository import LinkRepository
from app.repositories.notes_repository import NotesRepository
from app.schemas.note_schema import NoteCreate, NoteUpdate
from app.services.link_parser import extract_wiki_links
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.messaging.producer import publish_event

logger = logging.getLogger(__name__)

_CACHE_TTL = 300  # 5 minutes — Sprint 6 §18


def _list_cache_key(user_id: UUID, page: int, limit: int) -> str:
    return f"notes:user:{user_id}:page:{page}:{limit}"


def _user_cache_pattern(user_id: UUID) -> str:
    return f"notes:user:{user_id}:*"


class NotesService:
    """Core business logic for Notes Service."""

    def __init__(self, session: AsyncSession, redis=None):
        self.repo = NotesRepository(session)
        self.links = LinkRepository(session)
        self.redis = redis

    def _sanitize(self, content_md: str) -> str:
        """Strip dangerous HTML — Sprint 6 §20."""
        return nh3.clean(content_md)

    async def _invalidate_user_cache(self, user_id: UUID) -> None:
        if self.redis is None:
            return
        try:
            keys = await self.redis.keys(_user_cache_pattern(user_id))
            if keys:
                await self.redis.delete(*keys)
        except Exception:
            logger.warning(
                "Cache invalidation failed for user %s", user_id, exc_info=True
            )

    async def _process_wiki_links(self, note: Note, user_id: UUID) -> None:
        """Parse [[...]] links, resolve titles, create NoteLinks — Sprint 6 §8."""
        for title in extract_wiki_links(note.content_md):
            target = await self.repo.find_by_title(user_id, title)
            if target is None or target.id == note.id:
                continue
            already_exists = await self.links.link_exists(note.id, target.id)
            await self.links.create_link(note.id, target.id)
            if not already_exists:
                await publish_event(
                    NoteLinkCreatedEvent(
                        payload={
                            "source_note_id": str(note.id),
                            "target_note_id": str(target.id),
                            "user_id": str(user_id),
                        }
                    ),
                    key=str(user_id),
                )

    async def create_note(self, user_id: UUID, data: NoteCreate) -> Note:
        note = await self.repo.create(
            user_id=user_id,
            title=data.title,
            content_md=self._sanitize(data.content_md),
        )
        if data.tags:
            await self.repo.set_note_tags(note.id, data.tags)

        await self._process_wiki_links(note, user_id)
        await self._invalidate_user_cache(user_id)

        tags = await self.repo.list_note_tag_names(note.id)
        await publish_event(
            NoteCreatedEvent(
                payload={
                    "note_id": str(note.id),
                    "user_id": str(user_id),
                    "title": note.title,
                    "content_md": note.content_md,
                    "tags": tags,
                }
            ),
            key=str(user_id),
        )
        return note

    async def get_note(self, note_id: UUID) -> Optional[Note]:
        return await self.repo.get_by_id(note_id)

    async def list_notes(
        self, user_id: UUID, page: int = 1, limit: int = 50
    ) -> tuple[list[Note], int]:
        """List notes with page-based pagination — Sprint 6 §19."""
        offset = (page - 1) * limit
        cache_key = _list_cache_key(user_id, page, limit)

        if self.redis is not None:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    note_ids = data["note_ids"]
                    total = data["total"]
                    notes = [
                        n
                        for nid in note_ids
                        if (n := await self.repo.get_by_id(UUID(nid)))
                    ]
                    return notes, total
            except Exception:
                logger.warning("Cache read failed", exc_info=True)

        notes, total = await self.repo.list_by_user(user_id, offset, limit)

        if self.redis is not None:
            try:
                await self.redis.set(
                    cache_key,
                    json.dumps(
                        {"note_ids": [str(n.id) for n in notes], "total": total}
                    ),
                    ex=_CACHE_TTL,
                )
            except Exception:
                logger.warning("Cache write failed", exc_info=True)

        return notes, total

    async def update_note(self, note: Note, data: NoteUpdate) -> Note:
        updates = data.model_dump(exclude_unset=True, exclude={"tags"})
        if "content_md" in updates and updates["content_md"] is not None:
            updates["content_md"] = self._sanitize(updates["content_md"])

        note = await self.repo.update(note, **updates)

        if data.tags is not None:
            await self.repo.set_note_tags(note.id, data.tags)
        if data.content_md is not None:
            await self._process_wiki_links(note, note.user_id)

        await self._invalidate_user_cache(note.user_id)

        tags = await self.repo.list_note_tag_names(note.id)
        await publish_event(
            NoteUpdatedEvent(
                payload={
                    "note_id": str(note.id),
                    "user_id": str(note.user_id),
                    "title": note.title,
                    "content_md": note.content_md,
                    "tags": tags,
                }
            ),
            key=str(note.user_id),
        )
        return note

    async def delete_note(self, note: Note) -> None:
        user_id = note.user_id
        note_id = str(note.id)
        await self.repo.delete(note)
        await self._invalidate_user_cache(user_id)
        await publish_event(
            NoteDeletedEvent(payload={"note_id": note_id, "user_id": str(user_id)}),
            key=str(user_id),
        )

    async def link_notes(self, source_id: UUID, target_id: UUID, user_id: UUID):
        link = await self.links.create_link(source_id, target_id)
        await publish_event(
            NoteLinkCreatedEvent(
                payload={
                    "source_note_id": str(source_id),
                    "target_note_id": str(target_id),
                    "user_id": str(user_id),
                }
            ),
            key=str(user_id),
        )
        return link

    async def get_backlinks(self, note_id: UUID) -> list[Note]:
        return await self.links.get_backlinks(note_id)
