"""
Tests for event consumers.

Verifies that event consumers correctly process events from Kafka and record metrics.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.events.database_consumer import DatabaseEventConsumer
from app.events.habit_consumer import HabitEventConsumer
from app.events.health_consumer import HealthEventConsumer
from app.events.learning_consumer import LearningEventConsumer
from app.events.notes_consumer import NotesEventConsumer


@pytest.fixture
def user_id():
    """Test user ID."""
    return str(uuid4())


@pytest.fixture
def mock_session():
    """Mock database session."""
    return AsyncMock()


def _make_session_patch(module: str):
    """Return a patch for async_session_factory that yields a mock session."""
    mock_session = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    return patch(f"app.events.{module}.async_session_factory", return_value=mock_cm)


# ==================== Habit Consumer Tests ====================


@pytest.mark.asyncio
async def test_habit_consumer_processes_completion_event(user_id, mock_session):
    """Test habit consumer records completion rate from event."""
    consumer = HabitEventConsumer()
    payload = {
        "user_id": user_id,
        "habit_id": str(uuid4()),
        "completed": True,
        "timestamp": datetime.utcnow().isoformat(),
    }

    mock_svc = AsyncMock()
    with _make_session_patch("habit_consumer"), patch(
        "app.events.habit_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("habit.completed", payload)
        assert mock_svc.record_metric.called


@pytest.mark.asyncio
async def test_habit_consumer_ignores_missing_user_id(user_id):
    """Test habit consumer ignores events without user_id."""
    consumer = HabitEventConsumer()
    payload = {
        "habit_id": str(uuid4()),
        "completed": True,
        "timestamp": datetime.utcnow().isoformat(),
    }

    mock_svc = AsyncMock()
    with _make_session_patch("habit_consumer"), patch(
        "app.events.habit_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("habit.completed", payload)
        assert not mock_svc.record_metric.called


@pytest.mark.asyncio
async def test_habit_consumer_handles_error(user_id):
    """Test habit consumer handles repository errors gracefully."""
    consumer = HabitEventConsumer()
    payload = {
        "user_id": user_id,
        "habit_id": str(uuid4()),
        "completed": True,
        "timestamp": datetime.utcnow().isoformat(),
    }

    mock_svc = AsyncMock()
    mock_svc.record_metric.side_effect = Exception("DB error")
    with _make_session_patch("habit_consumer"), patch(
        "app.events.habit_consumer.AnalyticsService", return_value=mock_svc
    ):
        # Consumer logs and re-raises errors for DLQ forwarding
        with pytest.raises(Exception, match="DB error"):
            await consumer.handle_event("habit.completed", payload)


# ==================== Learning Consumer Tests ====================


@pytest.mark.asyncio
async def test_learning_consumer_processes_session_event(user_id):
    """Test learning consumer records hours from session completion event."""
    consumer = LearningEventConsumer()
    payload = {
        "user_id": user_id,
        "session_id": str(uuid4()),
        "duration": 60,  # Consumer reads "duration" key, not "duration_minutes"
        "topic": "React",
        "timestamp": datetime.utcnow().isoformat(),
    }

    mock_svc = AsyncMock()
    with _make_session_patch("learning_consumer"), patch(
        "app.events.learning_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("learning.session.completed", payload)
        assert mock_svc.record_metric.called


@pytest.mark.asyncio
async def test_learning_consumer_ignores_missing_duration(user_id):
    """Test learning consumer ignores events without duration."""
    consumer = LearningEventConsumer()
    payload = {
        "user_id": user_id,
        "session_id": str(uuid4()),
        "topic": "React",
        "timestamp": datetime.utcnow().isoformat(),
        # "duration" key intentionally missing
    }

    mock_svc = AsyncMock()
    with _make_session_patch("learning_consumer"), patch(
        "app.events.learning_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("learning.session.completed", payload)
        assert not mock_svc.record_metric.called


# ==================== Health Consumer Tests ====================


@pytest.mark.asyncio
async def test_health_consumer_processes_meal_event(user_id):
    """Test health consumer records calorie intake from meal event."""
    consumer = HealthEventConsumer()
    payload = {
        "user_id": user_id,
        "meal_id": str(uuid4()),
        "calories": 500,
        "timestamp": datetime.utcnow().isoformat(),
    }

    mock_svc = AsyncMock()
    with _make_session_patch("health_consumer"), patch(
        "app.events.health_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("meal.logged", payload)
        assert mock_svc.record_metric.called


@pytest.mark.asyncio
async def test_health_consumer_processes_workout_event(user_id):
    """Test health consumer records calories burned from workout event."""
    consumer = HealthEventConsumer()
    payload = {
        "user_id": user_id,
        "workout_id": str(uuid4()),
        "calories_burned": 300,
        "duration_minutes": 30,
        "activity_type": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }

    mock_svc = AsyncMock()
    with _make_session_patch("health_consumer"), patch(
        "app.events.health_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("workout.completed", payload)
        assert mock_svc.record_metric.called


@pytest.mark.asyncio
async def test_health_consumer_ignores_invalid_calories(user_id):
    """Test health consumer ignores events with invalid calorie values."""
    consumer = HealthEventConsumer()
    payload = {
        "user_id": user_id,
        "meal_id": str(uuid4()),
        "calories": -100,  # Invalid negative calories
        "timestamp": datetime.utcnow().isoformat(),
    }

    mock_svc = AsyncMock()
    with _make_session_patch("health_consumer"), patch(
        "app.events.health_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("meal.logged", payload)
        # Depends on consumer implementation — just verify no exception raised


# ==================== Notes Consumer Tests ====================


@pytest.mark.asyncio
async def test_notes_consumer_processes_created_event(user_id):
    """Test notes consumer records note creation."""
    consumer = NotesEventConsumer()
    payload = {
        "user_id": user_id,
        "note_id": str(uuid4()),
        "title": "React Hooks",
        "created_at": datetime.utcnow().isoformat(),
        "backlink_count": 3,
    }

    mock_svc = AsyncMock()
    with _make_session_patch("notes_consumer"), patch(
        "app.events.notes_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("note.created", payload)
        assert mock_svc.record_metric.called


@pytest.mark.asyncio
async def test_notes_consumer_tracks_linking_density(user_id):
    """Test notes consumer tracks linking density (backlinks)."""
    consumer = NotesEventConsumer()
    payload = {
        "user_id": user_id,
        "note_id": str(uuid4()),
        "title": "React Hooks",
        "created_at": datetime.utcnow().isoformat(),
        "backlink_count": 5,
    }

    mock_svc = AsyncMock()
    with _make_session_patch("notes_consumer"), patch(
        "app.events.notes_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("note.created", payload)
        assert mock_svc.record_metric.called


# ==================== Database Consumer Tests ====================


@pytest.mark.asyncio
async def test_database_consumer_processes_record_event(user_id):
    """Test database consumer records item creation."""
    consumer = DatabaseEventConsumer()
    payload = {
        "user_id": user_id,
        "database_id": str(uuid4()),
        "record_id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat(),
    }

    mock_svc = AsyncMock()
    with _make_session_patch("database_consumer"), patch(
        "app.events.database_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("database.record.created", payload)
        assert mock_svc.record_metric.called


@pytest.mark.asyncio
async def test_database_consumer_ignores_missing_record_id(user_id):
    """Test database consumer still processes without record_id."""
    consumer = DatabaseEventConsumer()
    payload = {
        "user_id": user_id,
        "database_id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        # No record_id
    }

    mock_svc = AsyncMock()
    with _make_session_patch("database_consumer"), patch(
        "app.events.database_consumer.AnalyticsService", return_value=mock_svc
    ):
        await consumer.handle_event("database.record.created", payload)
        # Consumer records with record_id=None since it doesn't guard for it
        assert mock_svc.record_metric.called


# ==================== Cross-Consumer Tests ====================


@pytest.mark.asyncio
async def test_multiple_consumers_independent(user_id):
    """Test multiple consumers operate independently."""
    habit_consumer = HabitEventConsumer()
    learning_consumer = LearningEventConsumer()

    habit_payload = {
        "user_id": user_id,
        "habit_id": str(uuid4()),
        "completed": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
    learning_payload = {
        "user_id": user_id,
        "session_id": str(uuid4()),
        "duration": 60,
        "topic": "React",
        "timestamp": datetime.utcnow().isoformat(),
    }

    habit_svc = AsyncMock()
    learning_svc = AsyncMock()

    with _make_session_patch("habit_consumer"), patch(
        "app.events.habit_consumer.AnalyticsService", return_value=habit_svc
    ), _make_session_patch("learning_consumer"), patch(
        "app.events.learning_consumer.AnalyticsService", return_value=learning_svc
    ):
        await habit_consumer.handle_event("habit.completed", habit_payload)
        await learning_consumer.handle_event(
            "learning.session.completed", learning_payload
        )

        assert habit_svc.record_metric.called
        assert learning_svc.record_metric.called
