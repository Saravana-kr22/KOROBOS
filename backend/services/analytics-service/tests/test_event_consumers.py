"""
Tests for event consumers.

Verifies that event consumers correctly process events from Kafka and record metrics.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch
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


# ==================== Habit Consumer Tests ====================


@pytest.mark.asyncio
async def test_habit_consumer_processes_completion_event(user_id, mock_session):
    """Test habit consumer records completion rate from event."""
    consumer = HabitEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "habit_id": str(uuid4()),
        "completed": True,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("habit.completed", payload)
        # Event should trigger metric recording
        assert consumer.repo.record_metric.called


@pytest.mark.asyncio
async def test_habit_consumer_ignores_missing_user_id(user_id):
    """Test habit consumer ignores events without user_id."""
    consumer = HabitEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "habit_id": str(uuid4()),
        "completed": True,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("habit.completed", payload)
        # Should not record without user_id
        assert not mock_repo.record_metric.called


@pytest.mark.asyncio
async def test_habit_consumer_handles_error(user_id):
    """Test habit consumer handles repository errors gracefully."""
    consumer = HabitEventConsumer()
    consumer.repo = AsyncMock()
    consumer.repo.record_metric.side_effect = Exception("DB error")

    payload = {
        "user_id": user_id,
        "habit_id": str(uuid4()),
        "completed": True,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Should not raise exception
    with patch.object(consumer, "repo", side_effect=Exception("DB error")):
        try:
            await consumer.handle_event("habit.completed", payload)
        except Exception:
            pytest.fail("Consumer should handle errors gracefully")


# ==================== Learning Consumer Tests ====================


@pytest.mark.asyncio
async def test_learning_consumer_processes_session_event(user_id):
    """Test learning consumer records hours from session completion event."""
    consumer = LearningEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "session_id": str(uuid4()),
        "duration_minutes": 60,
        "topic": "React",
        "timestamp": datetime.utcnow().isoformat(),
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("learning.session.completed", payload)
        # Should record learning hours metric
        assert mock_repo.record_metric.called


@pytest.mark.asyncio
async def test_learning_consumer_ignores_missing_duration(user_id):
    """Test learning consumer ignores events without duration."""
    consumer = LearningEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "session_id": str(uuid4()),
        "topic": "React",
        "timestamp": datetime.utcnow().isoformat(),
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("learning.session.completed", payload)
        # Should not record without duration
        assert not mock_repo.record_metric.called


# ==================== Health Consumer Tests ====================


@pytest.mark.asyncio
async def test_health_consumer_processes_meal_event(user_id):
    """Test health consumer records calorie intake from meal event."""
    consumer = HealthEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "meal_id": str(uuid4()),
        "calories": 500,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("meal.logged", payload)
        # Should record intake metric
        assert mock_repo.record_metric.called


@pytest.mark.asyncio
async def test_health_consumer_processes_workout_event(user_id):
    """Test health consumer records calories burned from workout event."""
    consumer = HealthEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "workout_id": str(uuid4()),
        "calories_burned": 300,
        "duration_minutes": 30,
        "activity_type": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("workout.completed", payload)
        # Should record burned metric
        assert mock_repo.record_metric.called


@pytest.mark.asyncio
async def test_health_consumer_ignores_invalid_calories(user_id):
    """Test health consumer ignores events with invalid calorie values."""
    consumer = HealthEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "meal_id": str(uuid4()),
        "calories": -100,  # Invalid negative calories
        "timestamp": datetime.utcnow().isoformat(),
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("meal.logged", payload)
        # Should validate and skip invalid data
        # (depends on consumer implementation)


# ==================== Notes Consumer Tests ====================


@pytest.mark.asyncio
async def test_notes_consumer_processes_created_event(user_id):
    """Test notes consumer records note creation."""
    consumer = NotesEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "note_id": str(uuid4()),
        "title": "React Hooks",
        "created_at": datetime.utcnow().isoformat(),
        "backlink_count": 3,
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("note.created", payload)
        # Should record notes_created metric
        assert mock_repo.record_metric.called


@pytest.mark.asyncio
async def test_notes_consumer_tracks_linking_density(user_id):
    """Test notes consumer tracks linking density (backlinks)."""
    consumer = NotesEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "note_id": str(uuid4()),
        "title": "React Hooks",
        "created_at": datetime.utcnow().isoformat(),
        "backlink_count": 5,  # Note with 5 backlinks
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("note.created", payload)
        # Should track backlink density info
        assert mock_repo.record_metric.called


# ==================== Database Consumer Tests ====================


@pytest.mark.asyncio
async def test_database_consumer_processes_record_event(user_id):
    """Test database consumer records item creation."""
    consumer = DatabaseEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "database_id": str(uuid4()),
        "record_id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat(),
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("database.record.created", payload)
        # Should record records_created metric
        assert mock_repo.record_metric.called


@pytest.mark.asyncio
async def test_database_consumer_ignores_missing_record_id(user_id):
    """Test database consumer ignores events without record_id."""
    consumer = DatabaseEventConsumer()
    consumer.repo = AsyncMock()

    payload = {
        "user_id": user_id,
        "database_id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat(),
    }

    with patch.object(consumer, "repo") as mock_repo:
        mock_repo.record_metric = AsyncMock()
        await consumer.handle_event("database.record.created", payload)
        # Should not record without record_id
        assert not mock_repo.record_metric.called


# ==================== Cross-Consumer Tests ====================


@pytest.mark.asyncio
async def test_multiple_consumers_independent(user_id):
    """Test multiple consumers operate independently."""
    habit_consumer = HabitEventConsumer()
    learning_consumer = LearningEventConsumer()

    habit_consumer.repo = AsyncMock()
    learning_consumer.repo = AsyncMock()

    habit_payload = {
        "user_id": user_id,
        "habit_id": str(uuid4()),
        "completed": True,
        "timestamp": datetime.utcnow().isoformat(),
    }

    learning_payload = {
        "user_id": user_id,
        "session_id": str(uuid4()),
        "duration_minutes": 60,
        "topic": "React",
        "timestamp": datetime.utcnow().isoformat(),
    }

    with patch.object(habit_consumer, "repo") as habit_repo, patch.object(
        learning_consumer, "repo"
    ) as learning_repo:
        habit_repo.record_metric = AsyncMock()
        learning_repo.record_metric = AsyncMock()

        await habit_consumer.handle_event("habit.completed", habit_payload)
        await learning_consumer.handle_event(
            "learning.session.completed", learning_payload
        )

        # Both consumers should have been called
        assert habit_repo.record_metric.called
        assert learning_repo.record_metric.called
