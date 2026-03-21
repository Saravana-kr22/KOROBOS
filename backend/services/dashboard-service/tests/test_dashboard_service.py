"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for Dashboard Service business logic.
"""

from unittest.mock import patch
from uuid import uuid4

import pytest
from app.schemas.dashboard_schema import DailyMetrics
from app.services.dashboard_service import DashboardService
from app.services.metric_engine import MetricEngine


@pytest.mark.asyncio
class TestMetricEngine:
    """Test MetricEngine calculations."""

    async def test_productivity_score_perfect(self):
        """Perfect score: all domains at 100."""
        score = MetricEngine.compute_productivity_score(100.0, 100.0, 100.0)
        assert score == 100

    async def test_productivity_score_zero(self):
        """Zero score: no activity."""
        score = MetricEngine.compute_productivity_score(0.0, 0.0, 0.0)
        assert score == 0

    async def test_productivity_score_capped(self):
        """Score capped at 100."""
        score = MetricEngine.compute_productivity_score(150.0, 150.0, 150.0)
        assert score == 100

    async def test_habit_score_with_habits(self):
        """Habit score calculation with completed habits."""
        score = MetricEngine.habit_score(3, 5)
        assert score == 60.0

    async def test_habit_score_no_habits(self):
        """Habit score when no habits defined."""
        score = MetricEngine.habit_score(0, 0)
        assert score == 0.0

    async def test_learning_score_meets_target(self):
        """Learning score at target (60 min)."""
        score = MetricEngine.learning_score(60)
        assert score == 100.0

    async def test_learning_score_exceeds_target(self):
        """Learning score capped at 100 when exceeding target."""
        score = MetricEngine.learning_score(120)
        assert score == 100.0

    async def test_health_score_balanced(self):
        """Health score when net calories within tolerance."""
        score = MetricEngine.health_score(0)
        assert score == 100.0

    async def test_health_score_surplus(self):
        """Health score penalized for calorie surplus."""
        score = MetricEngine.health_score(500)
        assert score == 0.0  # At tolerance limit


@pytest.mark.asyncio
class TestDashboardService:
    """Test DashboardService orchestration."""

    async def test_get_daily_aggregates_all_sources(
        self,
        db_session,
        dashboard_settings,
        test_habit_response,
        test_health_response,
        test_learning_response,
    ):
        """get_daily aggregates data from all source services."""
        svc = DashboardService(db_session, dashboard_settings, redis_client=None)
        user_id = uuid4()

        with patch.object(svc.engine, "get_habit_data") as mock_habit:
            with patch.object(svc.engine, "get_health_data") as mock_health:
                with patch.object(svc.engine, "get_learning_data") as mock_learning:
                    mock_habit.return_value = test_habit_response
                    mock_health.return_value = test_health_response
                    mock_learning.return_value = test_learning_response

                    result = await svc.get_daily(user_id, {"X-User-ID": str(user_id)})

                    assert result.habits_completed == 3
                    assert result.total_habits == 5
                    assert result.calories_consumed == 2000
                    assert result.productivity_score >= 0
                    assert result.productivity_score <= 100
                    assert result.current_streak == 7

    async def test_get_overview_simplifies_daily(
        self,
        db_session,
        dashboard_settings,
        test_habit_response,
        test_health_response,
        test_learning_response,
    ):
        """get_overview returns simplified version of get_daily."""
        svc = DashboardService(db_session, dashboard_settings, redis_client=None)
        user_id = uuid4()

        with patch.object(svc.engine, "get_habit_data") as mock_habit:
            with patch.object(svc.engine, "get_health_data") as mock_health:
                with patch.object(svc.engine, "get_learning_data") as mock_learning:
                    mock_habit.return_value = test_habit_response
                    mock_health.return_value = test_health_response
                    mock_learning.return_value = test_learning_response

                    result = await svc.get_overview(
                        user_id, {"X-User-ID": str(user_id)}
                    )

                    assert result.habits_completed == 3
                    assert result.learning_minutes == 60
                    assert result.calories_balance == 1500
                    assert "total_habits" not in result.model_dump()

    async def test_graceful_degradation_habit_service_down(
        self,
        db_session,
        dashboard_settings,
        test_health_response,
        test_learning_response,
    ):
        """Dashboard returns zeros for habits if habit-service is down."""
        svc = DashboardService(db_session, dashboard_settings, redis_client=None)
        user_id = uuid4()

        with patch.object(svc.engine, "get_habit_data") as mock_habit:
            with patch.object(svc.engine, "get_health_data") as mock_health:
                with patch.object(svc.engine, "get_learning_data") as mock_learning:
                    mock_habit.return_value = {"habits_completed": 0, "total_habits": 0}
                    mock_health.return_value = test_health_response
                    mock_learning.return_value = test_learning_response

                    result = await svc.get_daily(user_id, {"X-User-ID": str(user_id)})

                    assert result.habits_completed == 0
                    assert result.calories_consumed == 2000
                    assert result.productivity_score >= 0

    async def test_get_daily_includes_notes_and_database_data(
        self,
        db_session,
        dashboard_settings,
        test_habit_response,
        test_health_response,
        test_learning_response,
    ):
        """get_daily includes notes and database metrics in response."""
        svc = DashboardService(db_session, dashboard_settings, redis_client=None)
        user_id = uuid4()

        test_notes_response = {"notes_created_today": 2, "total_notes": 15}
        test_database_response = {"total_databases": 3, "records_created_today": 5}

        with patch.object(svc.engine, "get_habit_data") as mock_habit:
            with patch.object(svc.engine, "get_health_data") as mock_health:
                with patch.object(svc.engine, "get_learning_data") as mock_learning:
                    with patch.object(svc.engine, "get_notes_data") as mock_notes:
                        with patch.object(
                            svc.engine, "get_database_data"
                        ) as mock_database:
                            mock_habit.return_value = test_habit_response
                            mock_health.return_value = test_health_response
                            mock_learning.return_value = test_learning_response
                            mock_notes.return_value = test_notes_response
                            mock_database.return_value = test_database_response

                            result = await svc.get_daily(
                                user_id, {"X-User-ID": str(user_id)}
                            )

                            assert result.notes_created_today == 2
                            assert result.records_created_today == 5

    async def test_notes_and_database_service_down_graceful_fallback(
        self,
        db_session,
        dashboard_settings,
        test_habit_response,
        test_health_response,
        test_learning_response,
    ):
        """Dashboard returns zeros for notes/database if services down."""
        svc = DashboardService(db_session, dashboard_settings, redis_client=None)
        user_id = uuid4()

        with patch.object(svc.engine, "get_habit_data") as mock_habit:
            with patch.object(svc.engine, "get_health_data") as mock_health:
                with patch.object(svc.engine, "get_learning_data") as mock_learning:
                    with patch.object(svc.engine, "get_notes_data") as mock_notes:
                        with patch.object(
                            svc.engine, "get_database_data"
                        ) as mock_database:
                            mock_habit.return_value = test_habit_response
                            mock_health.return_value = test_health_response
                            mock_learning.return_value = test_learning_response
                            mock_notes.return_value = {}
                            mock_database.return_value = {}

                            result = await svc.get_daily(
                                user_id, {"X-User-ID": str(user_id)}
                            )

                            assert result.notes_created_today == 0
                            assert result.records_created_today == 0
                            assert result.productivity_score >= 0

    async def test_cache_hit_bypasses_aggregation(
        self,
        db_session,
        dashboard_settings,
        test_habit_response,
        test_health_response,
        test_learning_response,
    ):
        """Cache hit returns cached data without calling aggregation engine."""
        from unittest.mock import AsyncMock

        import redis.asyncio as aioredis

        # Mock Redis with a cached response
        mock_redis = AsyncMock(spec=aioredis.Redis)
        cached_response = DailyMetrics(
            date="2026-03-22",
            habits_completed=3,
            total_habits=5,
            learning_minutes=60,
            calories_consumed=2000,
            calories_burned=500,
            net_calories=1500,
            productivity_score=78,
            notes_created_today=2,
            records_created_today=5,
        )
        mock_redis.get = AsyncMock(return_value=cached_response.model_dump_json())

        svc = DashboardService(db_session, dashboard_settings, redis_client=mock_redis)
        user_id = uuid4()

        # First call should hit cache
        result = await svc.get_daily(user_id, {"X-User-ID": str(user_id)})

        # Verify cache was checked
        mock_redis.get.assert_called_once()
        assert result.habits_completed == 3

    async def test_cache_miss_calls_aggregation(
        self,
        db_session,
        dashboard_settings,
        test_habit_response,
        test_health_response,
        test_learning_response,
    ):
        """Cache miss calls aggregation engine."""
        from unittest.mock import AsyncMock

        import redis.asyncio as aioredis

        # Mock Redis with no cached data
        mock_redis = AsyncMock(spec=aioredis.Redis)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        svc = DashboardService(db_session, dashboard_settings, redis_client=mock_redis)
        user_id = uuid4()

        with patch.object(svc.engine, "get_habit_data") as mock_habit:
            with patch.object(svc.engine, "get_health_data") as mock_health:
                with patch.object(svc.engine, "get_learning_data") as mock_learning:
                    with patch.object(svc.engine, "get_notes_data") as mock_notes:
                        with patch.object(
                            svc.engine, "get_database_data"
                        ) as mock_database:
                            mock_habit.return_value = test_habit_response
                            mock_health.return_value = test_health_response
                            mock_learning.return_value = test_learning_response
                            mock_notes.return_value = {
                                "notes_created_today": 0,
                                "total_notes": 0,
                            }
                            mock_database.return_value = {
                                "total_databases": 0,
                                "records_created_today": 0,
                            }

                            result = await svc.get_daily(
                                user_id, {"X-User-ID": str(user_id)}
                            )

                            # Verify aggregation was called (cache miss)
                            mock_habit.assert_called_once()
                            # Verify result was cached
                            mock_redis.set.assert_called_once()
                            assert result.habits_completed == 3
