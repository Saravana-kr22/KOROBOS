"""
KOROBOS — Database Service Route Integration Tests

Integration tests for the database API endpoints.
"""

import uuid

import httpx
import pytest
from app.main import app
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.shared.database.base_model import Base


@pytest.fixture
async def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_create_database_route():
    """Test POST /databases endpoint."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/databases",
            json={
                "name": "Test Database",
                "icon": "📊",
                "description": "A test database",
            },
            headers={"X-User-ID": str(user_id)},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Database"
    assert data["icon"] == "📊"
    assert data["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_list_databases_route():
    """Test GET /databases endpoint."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create a database first
        await client.post(
            "/databases",
            json={"name": "Test Database"},
            headers={"X-User-ID": str(user_id)},
        )

        # List databases
        response = await client.get(
            "/databases",
            headers={"X-User-ID": str(user_id)},
        )

    assert response.status_code == 200
    data = response.json()
    assert "databases" in data
    assert len(data["databases"]) >= 1


@pytest.mark.asyncio
async def test_get_database_route():
    """Test GET /databases/{id} endpoint."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create a database
        create_response = await client.post(
            "/databases",
            json={"name": "Test Database"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = create_response.json()["id"]

        # Get database
        get_response = await client.get(
            f"/databases/{db_id}",
            headers={"X-User-ID": str(user_id)},
        )

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == db_id
    assert data["name"] == "Test Database"


@pytest.mark.asyncio
async def test_update_database_route():
    """Test PUT /databases/{id} endpoint."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create a database
        create_response = await client.post(
            "/databases",
            json={"name": "Test Database"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = create_response.json()["id"]

        # Update database
        update_response = await client.put(
            f"/databases/{db_id}",
            json={"name": "Updated Database"},
            headers={"X-User-ID": str(user_id)},
        )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Database"


@pytest.mark.asyncio
async def test_delete_database_route():
    """Test DELETE /databases/{id} endpoint."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create a database
        create_response = await client.post(
            "/databases",
            json={"name": "Test Database"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = create_response.json()["id"]

        # Delete database
        delete_response = await client.delete(
            f"/databases/{db_id}",
            headers={"X-User-ID": str(user_id)},
        )

    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_unauthorized_access():
    """Test that accessing other user's database returns 404."""
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create database as user 1
        create_response = await client.post(
            "/databases",
            json={"name": "Test Database"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = create_response.json()["id"]

        # Try to access as user 2
        get_response = await client.get(
            f"/databases/{db_id}",
            headers={"X-User-ID": str(other_user_id)},
        )

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_add_property_route():
    """Test POST /databases/{id}/properties endpoint."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create a database
        create_response = await client.post(
            "/databases",
            json={"name": "Test Database"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = create_response.json()["id"]

        # Add property
        prop_response = await client.post(
            f"/databases/{db_id}/properties",
            json={
                "name": "Title",
                "type": "text",
            },
            headers={"X-User-ID": str(user_id)},
        )

    assert prop_response.status_code == 201
    data = prop_response.json()
    assert data["name"] == "Title"
    assert data["type"] == "text"


@pytest.mark.asyncio
async def test_create_record_route():
    """Test POST /databases/{id}/records endpoint."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create a database
        create_db = await client.post(
            "/databases",
            json={"name": "Test Database"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = create_db.json()["id"]

        # Add property
        create_prop = await client.post(
            f"/databases/{db_id}/properties",
            json={"name": "Title", "type": "text"},
            headers={"X-User-ID": str(user_id)},
        )
        prop_id = create_prop.json()["id"]

        # Create record
        record_response = await client.post(
            f"/databases/{db_id}/records",
            json={
                "values": {prop_id: "Test Title"},
            },
            headers={"X-User-ID": str(user_id)},
        )

    assert record_response.status_code == 201
    data = record_response.json()
    assert data["database_id"] == db_id
    assert len(data["values"]) == 1
    assert data["values"][0]["value"] == "Test Title"


@pytest.mark.asyncio
async def test_list_records_route():
    """Test GET /databases/{id}/records endpoint."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create a database
        create_db = await client.post(
            "/databases",
            json={"name": "Test Database"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = create_db.json()["id"]

        # List records
        list_response = await client.get(
            f"/databases/{db_id}/records",
            headers={"X-User-ID": str(user_id)},
        )

    assert list_response.status_code == 200
    data = list_response.json()
    assert "records" in data
    assert isinstance(data["records"], list)
