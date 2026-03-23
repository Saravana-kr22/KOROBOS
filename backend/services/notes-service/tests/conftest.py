"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

pytest fixtures for the Notes Service test suite.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from app.models.model import Base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """In-memory SQLite async session with notes-service schema."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(autouse=True)
def mock_publish():
    """Mock Kafka producer lifecycle."""
    with patch(
        "backend.shared.messaging.producer.get_producer", new_callable=AsyncMock
    ), patch(
        "backend.shared.messaging.producer.close_producer", new_callable=AsyncMock
    ), patch(
        "app.services.notes_service.publish_event", new_callable=AsyncMock
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Mock Redis globally for notes-service."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock(return_value=True)

    # Patch all Redis extraction points
    monkeypatch.setattr("app.api.notes_routes._get_redis", lambda r: mock_redis)
    monkeypatch.setattr(
        "app.api.rate_limit._redis_from_request", AsyncMock(return_value=mock_redis)
    )
    return mock_redis


@pytest.fixture
def sample_user_id() -> uuid.UUID:
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def other_user_id() -> uuid.UUID:
    return uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
