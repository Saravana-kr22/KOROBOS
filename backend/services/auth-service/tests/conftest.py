"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pytest configuration and fixtures for Auth Service tests.
"""

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import bcrypt
import pytest
import pytest_asyncio
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.shared.database.base_model import Base
from backend.shared.database.connection import get_db_session

# -- Passlib/Bcrypt 4.0+ Compatibility Patch --
_original_hashpw = bcrypt.hashpw


def _patched_hashpw(password, salt):
    if isinstance(password, str):
        password = password.encode("utf-8")
    return _original_hashpw(password[:72], salt)


bcrypt.hashpw = _patched_hashpw
# ---------------------------------------------


@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock external services like Kafka and Email."""
    with patch(
        "backend.shared.messaging.producer.publish_event", new_callable=AsyncMock
    ) as mock_publish, patch(
        "app.services.email_service.send_verification_email", new_callable=AsyncMock
    ) as mock_verify_email, patch(
        "app.services.email_service.send_password_reset_email", new_callable=AsyncMock
    ) as mock_reset_email, patch(
        "backend.shared.messaging.producer.get_producer", new_callable=AsyncMock
    ) as mock_get_producer:
        mock_get_producer.return_value = AsyncMock()
        yield {
            "publish_event": mock_publish,
            "send_verification_email": mock_verify_email,
            "send_password_reset_email": mock_reset_email,
        }


# Use in-memory SQLite for testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.begin() as conn:
        # Enable foreign keys for SQLite
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")

    # Create session factory

    AsyncSession(bind=engine, expire_on_commit=False)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database session dependency override."""

    async def override_get_db():
        return test_db

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User",
    }


@pytest.fixture
def weak_password_data():
    """Weak password test data."""
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "weak",  # Too short, no special chars, etc.
        "full_name": "Test User",
    }


@pytest.fixture
def test_login_data():
    """Test login data."""
    return {
        "email": "testuser@example.com",
        "password": "TestPassword123!",
    }
