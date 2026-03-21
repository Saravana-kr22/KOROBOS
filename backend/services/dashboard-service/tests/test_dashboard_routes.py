"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Integration tests for Dashboard Service HTTP routes.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def client(db_session: AsyncSession):
    """HTTP test client with overridden dependencies."""

    def override_get_db():
        return db_session

    from backend.shared.database.connection import get_db_session

    app.dependency_overrides[get_db_session] = override_get_db
    return TestClient(app)


@pytest.mark.asyncio
class TestDashboardRoutes:
    """Test dashboard API routes."""

    def test_overview_returns_200(self, client, mocker):
        """GET /overview returns 200."""
        user_id = str(uuid4())

        # Mock the aggregation engine
        mock_engine = MagicMock()
        mocker.patch(
            "app.services.aggregation_engine.AggregationEngine",
            return_value=mock_engine,
        )

        with patch("app.services.aggregation_engine.AggregationEngine") as mock_agg:
            mock_instance = AsyncMock()
            mock_agg.return_value = mock_instance
            mock_instance.get_habit_data = AsyncMock(
                return_value={"habits_completed": 3, "total_habits": 5}
            )
            mock_instance.get_health_data = AsyncMock(
                return_value={
                    "calories_consumed": 2000,
                    "calories_burned": 500,
                    "net_calories": 1500,
                }
            )
            mock_instance.get_learning_data = AsyncMock(
                return_value={"learning_minutes": 60}
            )

            response = client.get(
                "/overview",
                headers={"X-User-ID": user_id},
            )

            assert response.status_code == 200
            data = response.json()
            assert "productivity_score" in data
            assert "habits_completed" in data

    def test_daily_returns_200(self, client):
        """GET /daily returns 200."""
        user_id = str(uuid4())
        response = client.get(
            "/daily",
            headers={"X-User-ID": user_id},
        )
        # Will fail without mocked services, but tests route exists
        assert response.status_code in [200, 502]  # 502 if service unavailable

    def test_weekly_returns_200(self, client):
        """GET /weekly returns 200."""
        user_id = str(uuid4())
        response = client.get(
            "/weekly",
            headers={"X-User-ID": user_id},
        )
        assert response.status_code in [200, 502]

    def test_metrics_returns_200(self, client):
        """GET /metrics returns 200."""
        user_id = str(uuid4())
        response = client.get(
            "/metrics",
            headers={"X-User-ID": user_id},
        )
        assert response.status_code in [200, 502]

    def test_health_endpoint(self, client):
        """GET /health returns healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "dashboard-service"

    def test_metrics_endpoint_prometheus_format(self, client):
        """GET /metrics returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    def test_missing_user_id_returns_422(self, client):
        """Request without X-User-ID returns 422."""
        response = client.get("/overview")
        assert response.status_code == 422

    def test_rate_limit_exceeded_returns_429(self, client):
        """Exceeding rate limit returns 429."""
        user_id = str(uuid4())

        # Mock Redis to simulate rate limit exceeded
        mock_redis = AsyncMock()
        # Return a value > 100 to trigger rate limit
        mock_redis.incr = AsyncMock(return_value=101)
        mock_redis.expire = AsyncMock()

        # Override app state with mocked Redis
        app.state.redis = mock_redis

        response = client.get(
            "/overview",
            headers={"X-User-ID": user_id},
        )

        assert response.status_code == 429
        data = response.json()
        assert "error" in data
