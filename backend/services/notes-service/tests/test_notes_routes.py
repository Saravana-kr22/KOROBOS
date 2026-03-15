"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Integration tests for Notes Service API endpoints.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from app.main import app
from app.models.model import Base
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.shared.database.connection import get_db_session

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
USER_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OTHER_USER_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session

    with patch("app.services.service_logic.publish_event", new_callable=AsyncMock):
        with patch(
            "app.api.routes._get_redis", return_value=AsyncMock(return_value=None)
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def _headers(user_id: str = USER_ID) -> dict:
    return {"X-User-ID": user_id}


# -- POST /notes --


@pytest.mark.asyncio
async def test_create_note_returns_201(client):
    resp = await client.post(
        "/notes",
        json={"title": "My Note", "content_md": "Hello", "tags": ["test"]},
        headers=_headers(),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "My Note"
    assert "id" in body
    assert "tags" in body


@pytest.mark.asyncio
async def test_create_note_missing_title_returns_422(client):
    resp = await client.post(
        "/notes",
        json={"content_md": "no title"},
        headers=_headers(),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_note_missing_user_header_returns_422(client):
    resp = await client.post("/notes", json={"title": "Note", "content_md": ""})
    assert resp.status_code == 422


# -- GET /notes --


@pytest.mark.asyncio
async def test_list_notes_empty(client):
    resp = await client.get("/notes", headers=_headers())
    assert resp.status_code == 200
    assert resp.json() == {"notes": [], "total": 0}


@pytest.mark.asyncio
async def test_list_notes_returns_own_notes_only(client):
    await client.post(
        "/notes",
        json={"title": "Mine", "content_md": ""},
        headers=_headers(USER_ID),
    )
    await client.post(
        "/notes",
        json={"title": "Other", "content_md": ""},
        headers=_headers(OTHER_USER_ID),
    )

    resp = await client.get("/notes", headers=_headers(USER_ID))
    body = resp.json()
    assert body["total"] == 1
    assert body["notes"][0]["title"] == "Mine"


# -- GET /notes/{note_id} --


@pytest.mark.asyncio
async def test_get_note_found(client):
    create = await client.post(
        "/notes",
        json={"title": "Findable", "content_md": "body"},
        headers=_headers(),
    )
    note_id = create.json()["id"]

    resp = await client.get(f"/notes/{note_id}", headers=_headers())
    assert resp.status_code == 200
    assert resp.json()["id"] == note_id


@pytest.mark.asyncio
async def test_get_note_not_found_returns_404(client):
    resp = await client.get(f"/notes/{uuid.uuid4()}", headers=_headers())
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_note_wrong_user_returns_404(client):
    create = await client.post(
        "/notes",
        json={"title": "Private", "content_md": ""},
        headers=_headers(USER_ID),
    )
    note_id = create.json()["id"]

    resp = await client.get(f"/notes/{note_id}", headers=_headers(OTHER_USER_ID))
    assert resp.status_code == 404


# -- PUT /notes/{note_id} --


@pytest.mark.asyncio
async def test_update_note(client):
    create = await client.post(
        "/notes",
        json={"title": "Old", "content_md": "old body"},
        headers=_headers(),
    )
    note_id = create.json()["id"]

    resp = await client.put(
        f"/notes/{note_id}",
        json={"title": "New Title"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_update_note_not_found_returns_404(client):
    resp = await client.put(
        f"/notes/{uuid.uuid4()}",
        json={"title": "X"},
        headers=_headers(),
    )
    assert resp.status_code == 404


# -- DELETE /notes/{note_id} --


@pytest.mark.asyncio
async def test_delete_note_returns_204(client):
    create = await client.post(
        "/notes",
        json={"title": "Delete Me", "content_md": ""},
        headers=_headers(),
    )
    note_id = create.json()["id"]

    resp = await client.delete(f"/notes/{note_id}", headers=_headers())
    assert resp.status_code == 204

    resp = await client.get(f"/notes/{note_id}", headers=_headers())
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_note_not_found_returns_404(client):
    resp = await client.delete(f"/notes/{uuid.uuid4()}", headers=_headers())
    assert resp.status_code == 404


# -- POST /notes/{note_id}/links --


@pytest.mark.asyncio
async def test_create_link_returns_201(client):
    n1 = (
        await client.post(
            "/notes", json={"title": "A", "content_md": ""}, headers=_headers()
        )
    ).json()["id"]
    n2 = (
        await client.post(
            "/notes", json={"title": "B", "content_md": ""}, headers=_headers()
        )
    ).json()["id"]

    resp = await client.post(
        f"/notes/{n1}/links",
        json={"target_note_id": n2},
        headers=_headers(),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["source_note_id"] == n1
    assert body["target_note_id"] == n2


# -- GET /notes/{note_id}/backlinks --


@pytest.mark.asyncio
async def test_get_backlinks(client):
    target_id = (
        await client.post(
            "/notes", json={"title": "Target", "content_md": ""}, headers=_headers()
        )
    ).json()["id"]
    source_id = (
        await client.post(
            "/notes", json={"title": "Source", "content_md": ""}, headers=_headers()
        )
    ).json()["id"]

    await client.post(
        f"/notes/{source_id}/links",
        json={"target_note_id": target_id},
        headers=_headers(),
    )

    resp = await client.get(f"/notes/{target_id}/backlinks", headers=_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["backlinks"][0]["id"] == source_id


@pytest.mark.asyncio
async def test_get_backlinks_empty(client):
    note_id = (
        await client.post(
            "/notes", json={"title": "Lonely", "content_md": ""}, headers=_headers()
        )
    ).json()["id"]

    resp = await client.get(f"/notes/{note_id}/backlinks", headers=_headers())
    assert resp.status_code == 200
    assert resp.json() == {"backlinks": [], "total": 0}
