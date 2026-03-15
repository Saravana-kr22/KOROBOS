"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for NotesService business logic.
"""

import pytest
from app.schemas.schema import NoteCreate, NoteUpdate
from app.services.service_logic import NotesService

# -- Create --


@pytest.mark.asyncio
async def test_create_note_basic(db_session, mock_publish, sample_user_id):
    svc = NotesService(db_session)
    data = NoteCreate(title="Test Note", content_md="Hello world", tags=[])
    note = await svc.create_note(sample_user_id, data)
    await db_session.commit()

    assert note.id is not None
    assert note.title == "Test Note"
    assert note.user_id == sample_user_id
    mock_publish.assert_called_once()
    call_event = mock_publish.call_args[0][0]
    assert call_event.event_type == "note.created"


@pytest.mark.asyncio
async def test_create_note_with_tags(db_session, mock_publish, sample_user_id):
    svc = NotesService(db_session)
    data = NoteCreate(title="Tagged Note", content_md="content", tags=["ml", "ai"])
    note = await svc.create_note(sample_user_id, data)
    await db_session.commit()

    tags = await svc.repo.list_note_tag_names(note.id)
    assert sorted(tags) == ["ai", "ml"]


@pytest.mark.asyncio
async def test_create_note_sanitizes_html(db_session, mock_publish, sample_user_id):
    svc = NotesService(db_session)
    data = NoteCreate(
        title="XSS Test",
        content_md='<script>alert("xss")</script>Safe text',
        tags=[],
    )
    note = await svc.create_note(sample_user_id, data)
    await db_session.commit()

    assert "<script>" not in note.content_md
    assert "Safe text" in note.content_md


# -- Wiki-link auto-processing --


@pytest.mark.asyncio
async def test_wiki_link_creates_note_link(db_session, mock_publish, sample_user_id):
    svc = NotesService(db_session)

    # Create the target note first
    target = await svc.create_note(
        sample_user_id, NoteCreate(title="Deep Learning", content_md="target")
    )
    await db_session.commit()
    mock_publish.reset_mock()

    # Create source note with wiki-link
    source = await svc.create_note(
        sample_user_id,
        NoteCreate(
            title="ML Overview", content_md="See [[Deep Learning]] for details."
        ),
    )
    await db_session.commit()

    # note.created + note.link.created should both be published
    event_types = [c[0][0].event_type for c in mock_publish.call_args_list]
    assert "note.link.created" in event_types

    # Backlinks on the target should include source
    backlinks = await svc.get_backlinks(target.id)
    assert any(b.id == source.id for b in backlinks)


@pytest.mark.asyncio
async def test_wiki_link_unresolved_title_skipped(
    db_session, mock_publish, sample_user_id
):
    svc = NotesService(db_session)
    data = NoteCreate(title="Orphan", content_md="See [[Nonexistent Note]].")
    await svc.create_note(sample_user_id, data)
    await db_session.commit()

    event_types = [c[0][0].event_type for c in mock_publish.call_args_list]
    assert "note.link.created" not in event_types


# -- Update --


@pytest.mark.asyncio
async def test_update_note_title(db_session, mock_publish, sample_user_id):
    svc = NotesService(db_session)
    note = await svc.create_note(
        sample_user_id, NoteCreate(title="Old Title", content_md="body")
    )
    await db_session.commit()
    mock_publish.reset_mock()

    updated = await svc.update_note(note, NoteUpdate(title="New Title"))
    await db_session.commit()

    assert updated.title == "New Title"
    call_event = mock_publish.call_args[0][0]
    assert call_event.event_type == "note.updated"


@pytest.mark.asyncio
async def test_update_note_replaces_tags(db_session, mock_publish, sample_user_id):
    svc = NotesService(db_session)
    note = await svc.create_note(
        sample_user_id, NoteCreate(title="Note", content_md="", tags=["old"])
    )
    await db_session.commit()

    await svc.update_note(note, NoteUpdate(tags=["new1", "new2"]))
    await db_session.commit()

    tags = await svc.repo.list_note_tag_names(note.id)
    assert sorted(tags) == ["new1", "new2"]


# -- Delete --


@pytest.mark.asyncio
async def test_delete_note_publishes_event(db_session, mock_publish, sample_user_id):
    svc = NotesService(db_session)
    note = await svc.create_note(
        sample_user_id, NoteCreate(title="To Delete", content_md="")
    )
    await db_session.commit()
    mock_publish.reset_mock()

    await svc.delete_note(note)
    await db_session.commit()

    call_event = mock_publish.call_args[0][0]
    assert call_event.event_type == "note.deleted"
    assert call_event.payload["note_id"] == str(note.id)


# -- List & pagination --


@pytest.mark.asyncio
async def test_list_notes_pagination(db_session, mock_publish, sample_user_id):
    svc = NotesService(db_session)
    for i in range(5):
        await svc.create_note(
            sample_user_id, NoteCreate(title=f"Note {i}", content_md="")
        )
    await db_session.commit()

    notes, total = await svc.list_notes(sample_user_id, offset=0, limit=3)
    assert total == 5
    assert len(notes) == 3


@pytest.mark.asyncio
async def test_list_notes_user_isolation(
    db_session, mock_publish, sample_user_id, other_user_id
):
    svc = NotesService(db_session)
    await svc.create_note(sample_user_id, NoteCreate(title="Mine", content_md=""))
    await svc.create_note(other_user_id, NoteCreate(title="Theirs", content_md=""))
    await db_session.commit()

    notes, total = await svc.list_notes(sample_user_id)
    assert total == 1
    assert notes[0].title == "Mine"


# -- Backlinks --


@pytest.mark.asyncio
async def test_get_backlinks_returns_sources(db_session, mock_publish, sample_user_id):
    svc = NotesService(db_session)
    target = await svc.create_note(
        sample_user_id, NoteCreate(title="Target", content_md="")
    )
    source = await svc.create_note(
        sample_user_id, NoteCreate(title="Source", content_md="")
    )
    await db_session.commit()

    await svc.link_notes(source.id, target.id, sample_user_id)
    await db_session.commit()

    backlinks = await svc.get_backlinks(target.id)
    assert len(backlinks) == 1
    assert backlinks[0].id == source.id
