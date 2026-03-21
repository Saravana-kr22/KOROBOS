"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Notes Service API routes — Sprint 6 §11, §19, §21.
"""

import math
from datetime import date
from uuid import UUID

from app.api.rate_limit import check_write_rate_limit
from app.main import NOTES_CREATED, NOTES_DELETED, NOTES_UPDATED
from app.models.note_model import Note
from app.schemas.note_schema import (
    BacklinkListResponse,
    NoteCreate,
    NoteLinkCreate,
    NoteLinkResponse,
    NoteListResponse,
    NoteResponse,
    NoteStatsResponse,
    NoteUpdate,
)
from app.services.notes_service import NotesService
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()

_SERVICE_LABEL = "notes-service"


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    return UUID(x_user_id)


def _get_redis(request: Request):
    return getattr(request.app.state, "redis", None)


async def _build_note_response(note, repo) -> NoteResponse:
    tags = await repo.list_note_tag_names(note.id)
    data = NoteResponse.model_validate(note)
    data.tags = tags
    return data


# -- CRUD --


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
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """List notes with page-based pagination — Sprint 6 §19."""
    svc = NotesService(session, redis=_get_redis(request))
    notes, total = await svc.list_notes(user_id, page=page, limit=limit)
    note_responses = [await _build_note_response(n, svc.repo) for n in notes]
    return {
        "notes": note_responses,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, math.ceil(total / limit)),
    }


@router.get("/stats", response_model=NoteStatsResponse, tags=["Notes"])
async def get_note_stats(
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get note activity statistics for the user."""
    today = date.today()

    # Total notes count
    total_result = await session.execute(
        select(func.count(Note.id)).where(Note.user_id == user_id)
    )
    total_notes = total_result.scalar() or 0

    # Notes created today
    today_result = await session.execute(
        select(func.count(Note.id)).where(
            Note.user_id == user_id,
            func.date(Note.created_at) == today,
        )
    )
    notes_created_today = today_result.scalar() or 0

    return {
        "notes_created_today": notes_created_today,
        "total_notes": total_notes,
    }


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
    "/notes/{note_id}/backlinks", response_model=BacklinkListResponse, tags=["Notes"]
)
async def get_backlinks(
    request: Request,
    note_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Return all notes that link to this note — Sprint 6 §9."""
    svc = NotesService(session)
    note = await svc.get_note(note_id)
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    backlinks = await svc.get_backlinks(note_id)
    responses = [await _build_note_response(n, svc.repo) for n in backlinks]
    return {"backlinks": responses, "total": len(responses)}


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
