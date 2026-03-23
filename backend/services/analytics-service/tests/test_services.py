"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for Analytics Service business logic.
"""

from uuid import uuid4

import pytest
from app.services.service_logic import AnalyticsService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.shared.database.base_model import Base

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


@pytest.mark.asyncio
class TestAnalyticsService:
    """Test AnalyticsService methods."""

    async def test_record_metric(self, db_session):
        """Test recording a metric."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        metric = await svc.record_metric(
            user_id=user_id,
            metric_type="learning_hours",
            value=2.5,
            metadata={"session_id": "test123"},
        )

        assert metric.user_id == user_id
        assert metric.metric_type == "learning_hours"
        assert metric.value == 2.5
        assert metric.metadata_json["session_id"] == "test123"

    async def test_get_habit_metrics_zero(self, db_session):
        """Test getting habit metrics when no data exists."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        metrics = await svc.get_habit_metrics(user_id)

        assert metrics["completion_rate"] == 0.0
        assert metrics["current_streak"] == 0

    async def test_get_habit_metrics_with_data(self, db_session):
        """Test getting habit metrics with recorded data."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        await svc.record_metric(
            user_id=user_id, metric_type="habit_completion_rate", value=75.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="current_streak", value=5.0
        )
        await db_session.commit()

        metrics = await svc.get_habit_metrics(user_id)

        assert metrics["completion_rate"] == 75.0
        assert metrics["current_streak"] == 5

    async def test_get_health_metrics(self, db_session):
        """Test getting health metrics."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        # Record some calorie data
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_intake", value=2000.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_intake", value=2100.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_burned", value=500.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_burned", value=550.0
        )
        await db_session.commit()

        metrics = await svc.get_health_metrics(user_id)

        assert metrics["intake"] == 2050  # average
        assert metrics["burned"] == 525  # average
        assert metrics["balance"] == 1525

    async def test_get_knowledge_metrics(self, db_session):
        """Test getting knowledge metrics."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        await svc.record_metric(user_id=user_id, metric_type="notes_created", value=1.0)
        await svc.record_metric(user_id=user_id, metric_type="notes_created", value=1.0)
        await svc.record_metric(
            user_id=user_id, metric_type="records_created", value=1.0
        )
        await db_session.commit()

        metrics = await svc.get_knowledge_metrics(user_id)

        # get_knowledge_metrics returns average, not sum; avg of [1.0, 1.0] = 1.0
        assert metrics["notes_created"] == 1.0
        assert metrics["records_created"] == 1.0

    async def test_get_cross_domain_score(self, db_session):
        """Test computing cross-domain productivity score."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        # Record balanced metrics
        await svc.record_metric(
            user_id=user_id, metric_type="habit_completion_rate", value=100.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="learning_hours", value=1.0
        )  # 60 min
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_intake", value=2000.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_burned", value=500.0
        )
        await db_session.commit()

        score = await svc.get_cross_domain_score(user_id)

        # Formula: (habit*0.35) + (learning*0.3) + (health*0.25) + (knowledge*0.1)
        # With calorie_intake=2000, burned=500 → net=1500 → health_score=0
        # score = (100*0.35) + (100*0.3) + (0*0.25) + (0*0.1) = 65
        assert score == 65

    async def test_get_cross_domain_score_capped(self, db_session):
        """Test that cross-domain score is capped at 100."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        # Record metrics that would exceed 100
        await svc.record_metric(
            user_id=user_id, metric_type="habit_completion_rate", value=150.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="learning_hours", value=2.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_intake", value=1500.0
        )
        await svc.record_metric(
            user_id=user_id, metric_type="calorie_burned", value=500.0
        )
        await db_session.commit()

        score = await svc.get_cross_domain_score(user_id)

        assert score <= 100

    async def test_get_trend(self, db_session):
        """Test getting trend data."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        # Record multiple metrics
        for i in range(5):
            await svc.record_metric(
                user_id=user_id, metric_type="learning_hours", value=float(i)
            )
        await db_session.commit()

        trend = await svc.get_trend(user_id, "learning_hours", limit=5)

        assert trend["metric_type"] == "learning_hours"
        assert len(trend["values"]) == 5
        assert len(trend["labels"]) == 5
        # Values should be in ascending order (oldest first)
        assert trend["values"] == [0.0, 1.0, 2.0, 3.0, 4.0]

    async def test_get_moving_average(self, db_session):
        """Test computing moving average."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        # Record 7 metrics
        for i in range(1, 8):
            await svc.record_metric(
                user_id=user_id, metric_type="learning_hours", value=float(i)
            )
        await db_session.commit()

        moving_avg = await svc.get_moving_average(user_id, "learning_hours", days=7)

        # Average of 1-7 = 4.0
        assert moving_avg == 4.0

    async def test_get_moving_average_empty(self, db_session):
        """Test moving average with no data."""
        user_id = uuid4()
        svc = AnalyticsService(db_session)

        moving_avg = await svc.get_moving_average(user_id, "learning_hours", days=7)

        assert moving_avg == 0.0
