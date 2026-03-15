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


@pytest.fixture
def mock_publish():
    """Patch Kafka publish_event so tests don't need a broker."""
    with patch(
        "app.services.service_logic.publish_event", new_callable=AsyncMock
    ) as mock:
        yield mock


@pytest.fixture
def sample_user_id() -> uuid.UUID:
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def other_user_id() -> uuid.UUID:
    return uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
