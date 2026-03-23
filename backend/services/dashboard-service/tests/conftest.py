"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Test configuration for Dashboard Service.
"""

import os
import sys
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from app.config.settings import DashboardSettings
from app.models.dashboard_model import Base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure service root is on sys.path so `from app.X` imports work
_SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SERVICE_ROOT not in sys.path:
    sys.path.insert(0, _SERVICE_ROOT)

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory test database session."""
    engine = create_async_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def mock_publish():
    """Mock Kafka event publishing."""
    with patch(
        "backend.shared.messaging.producer.publish_event", new_callable=AsyncMock
    ) as mock:
        yield mock


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return str(uuid4())


@pytest.fixture
def dashboard_settings():
    """Dashboard service settings for tests."""
    return DashboardSettings(
        database_url=SQLALCHEMY_TEST_DATABASE_URL,
        redis_url="redis://localhost:6379/1",
        kafka_broker="localhost:9092",
        debug=True,
        environment="test",
    )


@pytest.fixture
def test_habit_response():
    """Mock habit service response."""
    return {
        "habits_completed": 3,
        "total_habits": 5,
        "current_streak": 7,
    }


@pytest.fixture
def test_health_response():
    """Mock health service response."""
    return {
        "calories_consumed": 2000,
        "calories_burned": 500,
        "net_calories": 1500,
    }


@pytest.fixture
def test_learning_response():
    """Mock learning service response."""
    return {"learning_minutes": 60}
