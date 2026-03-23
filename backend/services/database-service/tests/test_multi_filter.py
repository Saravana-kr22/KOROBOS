"""
KOROBOS — Database Service Multi-Filter Tests

Tests for multiple filter support with AND logic.
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
async def test_single_filter():
    """Test filtering with a single condition."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create database
        db_resp = await client.post(
            "/databases",
            json={"name": "Tasks"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = db_resp.json()["id"]

        # Add properties
        status_prop = await client.post(
            f"/databases/{db_id}/properties",
            json={
                "name": "Status",
                "type": "select",
                "options": {"choices": ["TODO", "DONE"]},
            },
            headers={"X-User-ID": str(user_id)},
        )
        status_id = status_prop.json()["id"]

        # Create records
        await client.post(
            f"/databases/{db_id}/records",
            json={"values": {status_id: "TODO"}},
            headers={"X-User-ID": str(user_id)},
        )
        await client.post(
            f"/databases/{db_id}/records",
            json={"values": {status_id: "DONE"}},
            headers={"X-User-ID": str(user_id)},
        )

        # Filter for TODO
        list_resp = await client.get(
            f"/databases/{db_id}/records",
            params={
                "filter_property_id": status_id,
                "filter_value": "TODO",
            },
            headers={"X-User-ID": str(user_id)},
        )

    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert len(data["records"]) == 1


@pytest.mark.asyncio
async def test_multiple_filters_and_logic():
    """Test filtering with multiple conditions (AND logic)."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create database
        db_resp = await client.post(
            "/databases",
            json={"name": "Projects"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = db_resp.json()["id"]

        # Add properties
        status_prop = await client.post(
            f"/databases/{db_id}/properties",
            json={
                "name": "Status",
                "type": "select",
                "options": {"choices": ["Active", "Inactive"]},
            },
            headers={"X-User-ID": str(user_id)},
        )
        status_id = status_prop.json()["id"]

        priority_prop = await client.post(
            f"/databases/{db_id}/properties",
            json={"name": "Priority", "type": "number"},
            headers={"X-User-ID": str(user_id)},
        )
        priority_id = priority_prop.json()["id"]

        # Create records
        # Record 1: Active, Priority 3
        await client.post(
            f"/databases/{db_id}/records",
            json={"values": {status_id: "Active", priority_id: "3"}},
            headers={"X-User-ID": str(user_id)},
        )
        # Record 2: Active, Priority 1
        await client.post(
            f"/databases/{db_id}/records",
            json={"values": {status_id: "Active", priority_id: "1"}},
            headers={"X-User-ID": str(user_id)},
        )
        # Record 3: Inactive, Priority 3
        await client.post(
            f"/databases/{db_id}/records",
            json={"values": {status_id: "Inactive", priority_id: "3"}},
            headers={"X-User-ID": str(user_id)},
        )

        # Filter: Status=Active AND Priority>=2
        list_resp = await client.get(
            f"/databases/{db_id}/records",
            params={
                "filter_property_id": [status_id, priority_id],
                "filter_operator": ["eq", "gte"],
                "filter_value": ["Active", "2"],
            },
            headers={"X-User-ID": str(user_id)},
        )

    assert list_resp.status_code == 200
    data = list_resp.json()
    # Should return only Record 1 (Active AND Priority >= 2)
    assert data["total"] == 1
    assert len(data["records"]) == 1


@pytest.mark.asyncio
async def test_filter_with_contains_operator():
    """Test filtering with contains operator."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create database
        db_resp = await client.post(
            "/databases",
            json={"name": "Articles"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = db_resp.json()["id"]

        # Add property
        title_prop = await client.post(
            f"/databases/{db_id}/properties",
            json={"name": "Title", "type": "text"},
            headers={"X-User-ID": str(user_id)},
        )
        title_id = title_prop.json()["id"]

        # Create records
        await client.post(
            f"/databases/{db_id}/records",
            json={"values": {title_id: "Python Tutorial"}},
            headers={"X-User-ID": str(user_id)},
        )
        await client.post(
            f"/databases/{db_id}/records",
            json={"values": {title_id: "JavaScript Guide"}},
            headers={"X-User-ID": str(user_id)},
        )

        # Filter: Title contains "Python"
        list_resp = await client.get(
            f"/databases/{db_id}/records",
            params={
                "filter_property_id": title_id,
                "filter_operator": "contains",
                "filter_value": "Python",
            },
            headers={"X-User-ID": str(user_id)},
        )

    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_mismatched_filter_parameters():
    """Test error when filter parameter counts don't match."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create database
        db_resp = await client.post(
            "/databases",
            json={"name": "Test"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = db_resp.json()["id"]

        # Try to filter with mismatched parameter counts
        list_resp = await client.get(
            f"/databases/{db_id}/records",
            params={
                "filter_property_id": ["prop1", "prop2"],
                "filter_operator": ["eq"],  # Missing second operator
                "filter_value": ["val1", "val2"],
            },
            headers={"X-User-ID": str(user_id)},
        )

    # Should get 422 Unprocessable Entity
    assert list_resp.status_code == 422


@pytest.mark.asyncio
async def test_filter_empty_values_ignored():
    """Test that filters with empty values are ignored."""
    user_id = uuid.uuid4()

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create database
        db_resp = await client.post(
            "/databases",
            json={"name": "Items"},
            headers={"X-User-ID": str(user_id)},
        )
        db_id = db_resp.json()["id"]

        # Add property
        name_prop = await client.post(
            f"/databases/{db_id}/properties",
            json={"name": "Name", "type": "text"},
            headers={"X-User-ID": str(user_id)},
        )
        name_id = name_prop.json()["id"]

        # Create records
        await client.post(
            f"/databases/{db_id}/records",
            json={"values": {name_id: "Item A"}},
            headers={"X-User-ID": str(user_id)},
        )
        await client.post(
            f"/databases/{db_id}/records",
            json={"values": {name_id: "Item B"}},
            headers={"X-User-ID": str(user_id)},
        )

        # Filter with empty value (should be ignored)
        list_resp = await client.get(
            f"/databases/{db_id}/records",
            params={
                "filter_property_id": name_id,
                "filter_operator": "eq",
                "filter_value": "",  # Empty value
            },
            headers={"X-User-ID": str(user_id)},
        )

    assert list_resp.status_code == 200
    data = list_resp.json()
    # Both records should be returned since filter is ignored
    assert data["total"] == 2
