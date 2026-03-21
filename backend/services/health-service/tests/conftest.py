"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Test configuration for Health Service tests.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from app.main import app
from app.models.model import Base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.shared.database.connection import get_db_session

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["SERVICE_NAME"] = "health-service-test"
os.environ["HEALTH_REDIS_URL"] = "redis://localhost:6379/0"


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def mock_publish():
    """Mock Kafka event publishing."""
    with patch(
        "app.services.service_logic.publish_event", new_callable=AsyncMock
    ) as mock:
        yield mock


@pytest_asyncio.fixture
async def client(db_session):
    """Create a test HTTP client with dependency overrides."""

    async def override_get_db():
        return db_session

    app.dependency_overrides[get_db_session] = override_get_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_id():
    """Return a test user ID."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def test_meal_data():
    """Return test meal data."""
    return {
        "food_name": "Pasta",
        "calories": 500,
        "protein": 15,
        "carbs": 70,
        "fat": 10,
        "description": "Dinner pasta",
    }


@pytest.fixture
def test_workout_data():
    """Return test workout data."""
    return {
        "workout_type": "running",
        "duration": 30,
        "calories": 250,
        "description": "Morning run",
    }
