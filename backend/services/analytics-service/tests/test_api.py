"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

API endpoint tests for Analytics Service.
"""

from uuid import uuid4

import httpx
import pytest
from app.main import app
from app.services.service_logic import AnalyticsService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.shared.database.base_model import Base
from backend.shared.database.connection import get_db_session

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
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
async def test_client(db_session):
    """Create async FastAPI test client with dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestAnalyticsAPI:
    """Test Analytics Service API endpoints."""

    async def test_overview_endpoint(self, db_session, test_client):
        """Test GET /analytics/overview endpoint."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        # Record some metrics
        await svc.record_metric(
            user_id=user_id, metric_type="habit_completion_rate", value=80.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="learning_hours", value=1.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_intake", value=2000.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_burned", value=500.0
        )
        await db_session.commit()

        response = await test_client.get(
            "/analytics/overview",
            headers={"X-User-ID": str(user_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "productivity_score" in data["data"]
        assert "habits" in data["data"]
        assert "learning" in data["data"]
        assert "health" in data["data"]
        assert "knowledge" in data["data"]

    async def test_health_endpoint(self, db_session, test_client):
        """Test GET /analytics/health endpoint."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        # Record health metrics
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_intake", value=2000.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_burned", value=500.0
        )
        await db_session.commit()

        response = await test_client.get(
            "/analytics/health",
            headers={"X-User-ID": str(user_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "current" in data["data"]
        assert "intake_trend" in data["data"]
        assert "burned_trend" in data["data"]
        assert data["data"]["current"]["intake"] == 2000
        assert data["data"]["current"]["burned"] == 500

    async def test_trends_endpoint_7d(self, db_session, test_client):
        """Test GET /analytics/trends?period=7d endpoint."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        # Record metrics
        for i in range(7):
            await svc.record_metric(
                user_id=user_id, metric_type="learning_hours", value=float(i)
            )
        await db_session.commit()

        response = await test_client.get(
            "/analytics/trends?period=7d",
            headers={"X-User-ID": str(user_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "learning" in data["data"]
        assert len(data["data"]["learning"]["values"]) <= 7

    async def test_trends_endpoint_30d(self, db_session, test_client):
        """Test GET /analytics/trends?period=30d endpoint."""
        user_id = uuid4()

        response = await test_client.get(
            "/analytics/trends?period=30d",
            headers={"X-User-ID": str(user_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    async def test_trends_endpoint_90d(self, db_session, test_client):
        """Test GET /analytics/trends?period=90d endpoint."""
        user_id = uuid4()

        response = await test_client.get(
            "/analytics/trends?period=90d",
            headers={"X-User-ID": str(user_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    async def test_trends_invalid_period(self, db_session, test_client):
        """Test trends endpoint with invalid period parameter."""
        user_id = uuid4()

        response = await test_client.get(
            "/analytics/trends?period=invalid",
            headers={"X-User-ID": str(user_id)},
        )

        assert response.status_code == 422  # Validation error

    async def test_productivity_endpoint(self, db_session, test_client):
        """Test GET /analytics/productivity endpoint."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        await svc.record_metric(
            user_id=user_id, metric_type="productivity_score", value=85.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="habit_consistency", value=0.9
        )
        await svc.record_metric(
            user_id=user_id, metric_type="learning_hours", value=1.5
        )
        await db_session.commit()

        response = await test_client.get(
            "/analytics/productivity",
            headers={"X-User-ID": str(user_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["productivity_score"] == 85.0

    async def test_learning_growth_endpoint(self, db_session, test_client):
        """Test GET /analytics/learning-growth endpoint."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        for i in range(5):
            await svc.record_metric(
                user_id=user_id, metric_type="learning_hours", value=float(i)
            )
        await db_session.commit()

        response = await test_client.get(
            "/analytics/learning?limit=5",
            headers={"X-User-ID": str(user_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["metric_type"] == "learning_hours"
        assert len(data["data"]["values"]) == 5
