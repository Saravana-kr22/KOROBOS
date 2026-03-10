"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Notes Service API routes — full CRUD for notes and note linking.
"""

from uuid import UUID

from app.schemas.schema import (
    NoteCreate,
    NoteLinkCreate,
    NoteLinkResponse,
    NoteListResponse,
    NoteResponse,
    NoteUpdate,
)
from app.services.service_logic import NotesService
from backend.shared.database.connection import get_db_session
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header (injected by gateway)."""
    return UUID(x_user_id)


# -- CRUD Endpoints --


@router.post(
    "/notes",
    response_model=NoteResponse,
    status_code=201,
    tags=["Notes"],
)
async def create_note(
    data: NoteCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new note."""
    svc = NotesService(session)
    note = await svc.create_note(user_id, data)
    await session.commit()
    return note


@router.get("/notes", response_model=NoteListResponse, tags=["Notes"])
async def list_notes(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """List all notes for the authenticated user."""
    svc = NotesService(session)
    notes, total = await svc.list_notes(user_id, offset, limit)
    return {"notes": notes, "total": total}


@router.get("/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def get_note(
    note_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get a single note by ID."""
    svc = NotesService(session)
    note = await svc.get_note(note_id)
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def update_note(
    note_id: UUID,
    data: NoteUpdate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Update an existing note."""
    svc = NotesService(session)
    note = await svc.get_note(note_id)
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    updated = await svc.update_note(note, data)
    await session.commit()
    return updated


@router.delete("/notes/{note_id}", status_code=204, tags=["Notes"])
async def delete_note(
    note_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a note."""
    svc = NotesService(session)
    note = await svc.get_note(note_id)
    if not note or note.user_id != user_id:
        raise HTTPException(status_code=404, detail="Note not found")
    await svc.delete_note(note)
    await session.commit()


# -- Note Linking --


@router.post(
    "/notes/{note_id}/links",
    response_model=NoteLinkResponse,
    status_code=201,
    tags=["Notes"],
)
async def create_link(
    note_id: UUID,
    data: NoteLinkCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a link between two notes."""
    svc = NotesService(session)
    link = await svc.link_notes(note_id, data.target_note_id, user_id)
    await session.commit()
    return link


@router.get("/", tags=["Notes"])
async def root():
    return {"service": "notes-service", "status": "running"}
