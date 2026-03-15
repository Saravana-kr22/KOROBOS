"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Notes Service API routes — full CRUD for notes, note linking, and backlinks.
"""

from uuid import UUID

from app.api.rate_limit import check_write_rate_limit
from app.main import NOTES_CREATED, NOTES_DELETED, NOTES_UPDATED
from app.schemas.schema import (
    BacklinkListResponse,
    NoteCreate,
    NoteLinkCreate,
    NoteLinkResponse,
    NoteListResponse,
    NoteResponse,
    NoteUpdate,
)
from app.services.service_logic import NotesService
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()

_SERVICE_LABEL = "notes-service"


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header (injected by gateway)."""
    return UUID(x_user_id)


def _get_redis(request: Request):
    """Return the shared Redis client from app state (may be None)."""
    return getattr(request.app.state, "redis", None)


async def _build_note_response(note, repo) -> NoteResponse:
    """Attach tags to a note ORM object and return a NoteResponse."""
    tags = await repo.list_note_tag_names(note.id)
    data = NoteResponse.model_validate(note)
    data.tags = tags
    return data


# -- CRUD Endpoints --


@router.post("/notes", response_model=NoteResponse, status_code=201, tags=["Notes"])
async def create_note(
    request: Request,
    data: NoteCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new note."""
    await check_write_rate_limit(request, user_id)
    svc = NotesService(session, redis=_get_redis(request))
    note = await svc.create_note(user_id, data)
    await session.commit()
    NOTES_CREATED.labels(service=_SERVICE_LABEL).inc()
    return await _build_note_response(note, svc.repo)


@router.get("/notes", response_model=NoteListResponse, tags=["Notes"])
async def list_notes(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """List all notes for the authenticated user."""
    svc = NotesService(session, redis=_get_redis(request))
    notes, total = await svc.list_notes(user_id, offset, limit)
    note_responses = [await _build_note_response(n, svc.repo) for n in notes]
    return {"notes": note_responses, "total": total}


@router.get("/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def get_note(
    request: Request,
    note_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get a single note by ID."""
    svc = NotesService(session)
    note = await svc.get_note(note_id)
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    return await _build_note_response(note, svc.repo)


@router.put("/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def update_note(
    request: Request,
    note_id: UUID,
    data: NoteUpdate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Update an existing note."""
    await check_write_rate_limit(request, user_id)
    svc = NotesService(session, redis=_get_redis(request))
    note = await svc.get_note(note_id)
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    updated = await svc.update_note(note, data)
    await session.commit()
    NOTES_UPDATED.labels(service=_SERVICE_LABEL).inc()
    return await _build_note_response(updated, svc.repo)


@router.delete("/notes/{note_id}", status_code=204, tags=["Notes"])
async def delete_note(
    request: Request,
    note_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a note."""
    await check_write_rate_limit(request, user_id)
    svc = NotesService(session, redis=_get_redis(request))
    note = await svc.get_note(note_id)
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    await svc.delete_note(note)
    await session.commit()
    NOTES_DELETED.labels(service=_SERVICE_LABEL).inc()


# -- Backlinks --


@router.get(
    "/notes/{note_id}/backlinks",
    response_model=BacklinkListResponse,
    tags=["Notes"],
)
async def get_backlinks(
    request: Request,
    note_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Return all notes that link to this note."""
    svc = NotesService(session)
    note = await svc.get_note(note_id)
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    backlinks = await svc.get_backlinks(note_id)
    backlink_responses = [await _build_note_response(n, svc.repo) for n in backlinks]
    return {"backlinks": backlink_responses, "total": len(backlink_responses)}


# -- Note Linking --


@router.post(
    "/notes/{note_id}/links",
    response_model=NoteLinkResponse,
    status_code=201,
    tags=["Notes"],
)
async def create_link(
    request: Request,
    note_id: UUID,
    data: NoteLinkCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Create an explicit link between two notes."""
    svc = NotesService(session)
    link = await svc.link_notes(note_id, data.target_note_id, user_id)
    await session.commit()
    return link


@router.get("/", tags=["Notes"])
async def root():
    return {"service": "notes-service", "status": "running"}
