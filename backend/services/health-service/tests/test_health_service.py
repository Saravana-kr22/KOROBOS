"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for Health Service business logic.
"""

from datetime import date
from uuid import UUID

import pytest
from app.repositories.repository import HealthRepository
from app.schemas.schema import MealLogCreate, WorkoutLogCreate
from app.services.service_logic import HealthService


@pytest.mark.asyncio
class TestHealthService:
    """Test suite for HealthService."""

    @pytest.mark.asyncio
    async def test_log_meal(
        self, db_session, test_user_id, test_meal_data, mock_publish
    ):
        """Test logging a meal."""
        user_id = UUID(test_user_id)
        meal_data = MealLogCreate(**test_meal_data)

        svc = HealthService(db_session)
        log = await svc.log_meal(user_id, meal_data)

        assert log is not None
        assert log.user_id == user_id
        assert log.log_type == "meal"
        assert log.calories == test_meal_data["calories"]
        assert log.food_name == test_meal_data["food_name"]
        assert log.protein == test_meal_data["protein"]

    @pytest.mark.asyncio
    async def test_log_workout(
        self, db_session, test_user_id, test_workout_data, mock_publish
    ):
        """Test logging a workout."""
        user_id = UUID(test_user_id)
        workout_data = WorkoutLogCreate(**test_workout_data)

        svc = HealthService(db_session)
        log = await svc.log_workout(user_id, workout_data)

        assert log is not None
        assert log.user_id == user_id
        assert log.log_type == "workout"
        assert log.duration == test_workout_data["duration"]
        assert log.workout_type == test_workout_data["workout_type"]

    @pytest.mark.asyncio
    async def test_list_logs(
        self, db_session, test_user_id, test_meal_data, mock_publish
    ):
        """Test listing health logs."""
        user_id = UUID(test_user_id)
        meal_data = MealLogCreate(**test_meal_data)

        svc = HealthService(db_session)

        # Log a meal first
        await svc.log_meal(user_id, meal_data)

        # List logs
        logs, total = await svc.list_logs(user_id)

        assert total == 1
        assert len(logs) == 1
        assert logs[0].log_type == "meal"

    @pytest.mark.asyncio
    async def test_get_stats(
        self, db_session, test_user_id, test_meal_data, test_workout_data, mock_publish
    ):
        """Test getting lifetime health statistics."""
        user_id = UUID(test_user_id)
        meal_data = MealLogCreate(**test_meal_data)
        workout_data = WorkoutLogCreate(**test_workout_data)

        svc = HealthService(db_session)

        # Log meal and workout
        await svc.log_meal(user_id, meal_data)
        await svc.log_workout(user_id, workout_data)

        stats = await svc.get_stats(user_id)

        assert stats["total_meals"] == 1
        assert stats["total_workouts"] == 1
        assert stats["total_calories"] == test_meal_data["calories"]
        assert stats["total_workout_minutes"] == test_workout_data["duration"]

    @pytest.mark.asyncio
    async def test_get_daily_stats(
        self, db_session, test_user_id, test_meal_data, test_workout_data, mock_publish
    ):
        """Test getting daily calorie statistics."""
        user_id = UUID(test_user_id)
        meal_data = MealLogCreate(**test_meal_data)
        workout_data = WorkoutLogCreate(**test_workout_data)

        svc = HealthService(db_session)

        # Log meal and workout
        await svc.log_meal(user_id, meal_data)
        await svc.log_workout(user_id, workout_data)

        daily_stats = await svc.get_daily_stats(user_id, date.today())

        assert daily_stats["calories_consumed"] == test_meal_data["calories"]
        assert daily_stats["calories_burned"] == test_workout_data["calories"]
        assert daily_stats["net_calories"] == (
            test_meal_data["calories"] - test_workout_data["calories"]
        )

    @pytest.mark.asyncio
    async def test_delete_log_success(
        self, db_session, test_user_id, test_meal_data, mock_publish
    ):
        """Test deleting a log successfully."""
        user_id = UUID(test_user_id)
        meal_data = MealLogCreate(**test_meal_data)

        svc = HealthService(db_session)

        # Log a meal
        log = await svc.log_meal(user_id, meal_data)

        # Delete it
        await svc.delete_log(user_id, log.id)

        # Verify it's gone
        repo = HealthRepository(db_session)
        deleted_log = await repo.get_by_id(log.id)
        assert deleted_log is None

    @pytest.mark.asyncio
    async def test_delete_log_not_found(self, db_session, test_user_id):
        """Test deleting a non-existent log."""
        from uuid import uuid4

        user_id = UUID(test_user_id)
        fake_log_id = uuid4()

        svc = HealthService(db_session)
        result = await svc.delete_log(user_id, fake_log_id)

        # Should return None for not found
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_log_wrong_user(
        self, db_session, test_user_id, test_meal_data, mock_publish
    ):
        """Test deleting a log that belongs to another user."""
        from uuid import uuid4

        user_id = UUID(test_user_id)
        other_user_id = uuid4()
        meal_data = MealLogCreate(**test_meal_data)

        svc = HealthService(db_session)

        # Log meal as user 1
        log = await svc.log_meal(user_id, meal_data)

        # Try to delete as user 2
        result = await svc.delete_log(other_user_id, log.id)

        # Should return None (ownership mismatch)
        assert result is None
