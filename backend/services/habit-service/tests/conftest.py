"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Test configuration for Habit Service tests.
"""

import os
import sys
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the habit-service root to sys.path so `app.*` imports resolve
_SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SERVICE_ROOT not in sys.path:
    sys.path.insert(0, _SERVICE_ROOT)

# Set test environment variables
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("SERVICE_NAME", "habit-service-test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

# Test database URL
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Mock the database connection module before any app imports
@pytest.fixture(scope="session", autouse=True)
def mock_db_engine():
    """Mock the database engine creation at session scope."""
    with patch("backend.shared.database.connection.create_async_engine") as mock_engine:
        # Create a real in-memory engine for tests
        real_engine = create_async_engine(
            SQLALCHEMY_TEST_DATABASE_URL,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        mock_engine.return_value = real_engine
        yield mock_engine


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory test database session."""
    engine = create_async_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()
