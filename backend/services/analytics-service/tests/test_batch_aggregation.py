"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for batch aggregation service.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from app.services.batch_aggregation import BatchAggregationService
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
class TestBatchAggregation:
    """Test batch aggregation service."""

    async def test_daily_aggregation_empty(self, db_session):
        """Test daily aggregation with no metrics."""
        user_id = uuid4()
        batch_svc = BatchAggregationService(db_session)
        target_date = datetime.utcnow()

        summary = await batch_svc.aggregate_daily_summary(user_id, target_date)

        assert summary["date"] == target_date.date().isoformat()
        assert summary["habit_completion_rate_avg"] == 0.0
        assert summary["calorie_intake_total"] == 0.0
        assert summary["learning_hours_total"] == 0.0
        assert summary["notes_created_count"] == 0
        assert summary["records_created_count"] == 0

    async def test_daily_aggregation_with_metrics(self, db_session):
        """Test daily aggregation with various metrics."""
        user_id = uuid4()
        analytics_svc = AnalyticsService(db_session)
        batch_svc = BatchAggregationService(db_session)

        target_date = datetime.utcnow()

        # Record metrics for the day
        await analytics_svc.record_metric(
            user_id=user_id, metric_type="habit_completion_rate", value=80.0
        )
        await analytics_svc.record_metric(
            user_id=user_id, metric_type="habit_completion_rate", value=90.0
        )
        await analytics_svc.record_metric(
            user_id=user_id, metric_type="calorie_intake", value=2000.0
        )
        await analytics_svc.record_metric(
            user_id=user_id, metric_type="calorie_burned", value=500.0
        )
        await analytics_svc.record_metric(
            user_id=user_id, metric_type="learning_hours", value=1.5
        )
        await analytics_svc.record_metric(
            user_id=user_id, metric_type="notes_created", value=1.0
        )
        await analytics_svc.record_metric(
            user_id=user_id, metric_type="notes_created", value=1.0
        )
        await analytics_svc.record_metric(
            user_id=user_id, metric_type="records_created", value=1.0
        )
        await db_session.commit()

        summary = await batch_svc.aggregate_daily_summary(user_id, target_date)

        assert summary["habit_completion_rate_avg"] == 85.0  # (80 + 90) / 2
        assert summary["calorie_intake_total"] == 2000.0
        assert summary["calorie_burned_total"] == 500.0
        assert summary["learning_hours_total"] == 1.5
        assert summary["notes_created_count"] == 2
        assert summary["records_created_count"] == 1

    async def test_weekly_aggregation_empty(self, db_session):
        """Test weekly aggregation with no metrics."""
        user_id = uuid4()
        batch_svc = BatchAggregationService(db_session)

        # Get start of current week (Monday)
        today = datetime.utcnow()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        summary = await batch_svc.aggregate_weekly_summary(user_id, week_start)

        assert summary["week_start"] == week_start.date().isoformat()
        assert summary["habit_completion_rate_avg"] == 0.0
        assert summary["learning_hours_total"] == 0.0
        assert summary["notes_created_total"] == 0
        assert summary["records_created_total"] == 0

    async def test_weekly_aggregation_with_metrics(self, db_session):
        """Test weekly aggregation with metrics across 7 days."""
        user_id = uuid4()
        analytics_svc = AnalyticsService(db_session)
        batch_svc = BatchAggregationService(db_session)

        # Get start of current week (Monday)
        today = datetime.utcnow()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # Record metrics across the week
        for day_offset in range(7):
            await analytics_svc.record_metric(
                user_id=user_id, metric_type="habit_completion_rate", value=75.0
            )
            await analytics_svc.record_metric(
                user_id=user_id, metric_type="learning_hours", value=1.0
            )
            await analytics_svc.record_metric(
                user_id=user_id, metric_type="calorie_intake", value=2000.0
            )
            await analytics_svc.record_metric(
                user_id=user_id, metric_type="calorie_burned", value=500.0
            )
            await analytics_svc.record_metric(
                user_id=user_id, metric_type="notes_created", value=1.0
            )

        await db_session.commit()

        summary = await batch_svc.aggregate_weekly_summary(user_id, week_start)

        assert summary["habit_completion_rate_avg"] == 75.0
        assert summary["learning_hours_total"] == 7.0
        assert summary["calorie_balance_avg"] == 10500.0  # (2000 - 500) * 7
        assert summary["notes_created_total"] == 7
        assert summary["records_created_total"] == 0
