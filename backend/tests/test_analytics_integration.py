"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Integration tests for analytics service — event consumer and metric recording.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from backend.services.analytics_service.app.events.learning_consumer import (
    LearningEventConsumer,
)


@pytest.mark.anyio
async def test_learning_consumer_records_metric_on_session_completed():
    """Test learning_hours metric recorded on session.completed."""
    user_id = uuid4()
    session_id = uuid4()
    duration_minutes = 45
    topic = "Python Async Patterns"

    payload = {
        "session_id": str(session_id),
        "user_id": str(user_id),
        "topic": topic,
        "duration": duration_minutes,
    }

    consumer = LearningEventConsumer()

    with (
        patch(
            "backend.services.analytics_service.app.events.learning_consumer.AsyncSessionLocal"
        ) as mock_session_local,
        patch(
            "backend.services.analytics_service.app.events.learning_consumer.AnalyticsService"
        ) as mock_service_class,
    ):
        # Setup mock session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Setup mock service
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        # Call handler
        await consumer.handle_event("learning.session.completed", payload)

        # Verify AnalyticsService was instantiated with the session
        mock_service_class.assert_called_once_with(mock_session)

        # Verify record_metric was called with correct parameters
        mock_service.record_metric.assert_called_once()
        call_args = mock_service.record_metric.call_args
        assert call_args[1]["user_id"] == user_id
        assert call_args[1]["metric_type"] == "learning_hours"
        assert call_args[1]["value"] == pytest.approx(duration_minutes / 60.0, abs=0.01)
        assert call_args[1]["metadata"]["session_id"] == str(session_id)
        assert call_args[1]["metadata"]["topic"] == topic

        # Verify session was committed
        mock_session.commit.assert_called_once()


@pytest.mark.anyio
async def test_learning_consumer_records_metric_on_session_logged():
    """Test that learning consumer records learning_hours metric on session.logged."""
    user_id = uuid4()
    session_id = uuid4()
    duration_minutes = 30
    topic = "Data Structures"

    payload = {
        "session_id": str(session_id),
        "user_id": str(user_id),
        "topic": topic,
        "duration": duration_minutes,
        "notes": "Learned about trees and graphs",
    }

    consumer = LearningEventConsumer()

    with (
        patch(
            "backend.services.analytics_service.app.events.learning_consumer.AsyncSessionLocal"
        ) as mock_session_local,
        patch(
            "backend.services.analytics_service.app.events.learning_consumer.AnalyticsService"
        ) as mock_service_class,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        await consumer.handle_event("learning.session.logged", payload)

        mock_service.record_metric.assert_called_once()
        call_args = mock_service.record_metric.call_args
        assert call_args[1]["metric_type"] == "learning_hours"
        assert call_args[1]["value"] == pytest.approx(duration_minutes / 60.0, abs=0.01)


@pytest.mark.anyio
async def test_learning_consumer_handles_missing_user_id_gracefully():
    """Test that consumer skips event gracefully when user_id is missing."""
    payload = {
        "session_id": str(uuid4()),
        "topic": "Some Topic",
        "duration": 30,
    }

    consumer = LearningEventConsumer()

    with patch(
        "backend.services.analytics_service.app.events.learning_consumer.AsyncSessionLocal"
    ) as mock_session_local:
        # Should not raise, should return early
        await consumer.handle_event("learning.session.completed", payload)
        # SessionLocal should not be called
        mock_session_local.assert_not_called()


@pytest.mark.anyio
async def test_learning_consumer_handles_missing_duration_gracefully():
    """Test that consumer skips event gracefully when duration is missing."""
    payload = {
        "session_id": str(uuid4()),
        "user_id": str(uuid4()),
        "topic": "Some Topic",
    }

    consumer = LearningEventConsumer()

    with patch(
        "backend.services.analytics_service.app.events.learning_consumer.AsyncSessionLocal"
    ) as mock_session_local:
        # Should not raise, should return early
        await consumer.handle_event("learning.session.completed", payload)
        # SessionLocal should not be called
        mock_session_local.assert_not_called()


@pytest.mark.anyio
async def test_learning_consumer_handles_invalid_user_id_format():
    """Test that consumer handles invalid UUID format in user_id."""
    payload = {
        "session_id": str(uuid4()),
        "user_id": "not-a-uuid",
        "topic": "Some Topic",
        "duration": 30,
    }

    consumer = LearningEventConsumer()

    with patch(
        "backend.services.analytics_service.app.events.learning_consumer.AsyncSessionLocal"
    ):
        # Should not raise, should handle gracefully
        await consumer.handle_event("learning.session.completed", payload)


@pytest.mark.anyio
async def test_learning_consumer_persists_metadata():
    """Test that consumer includes comprehensive metadata in recorded metric."""
    user_id = uuid4()
    session_id = uuid4()
    payload = {
        "session_id": str(session_id),
        "user_id": str(user_id),
        "topic": "Advanced React",
        "duration": 60,
    }

    consumer = LearningEventConsumer()

    with (
        patch(
            "backend.services.analytics_service.app.events.learning_consumer.AsyncSessionLocal"
        ) as mock_session_local,
        patch(
            "backend.services.analytics_service.app.events.learning_consumer.AnalyticsService"
        ) as mock_service_class,
    ):
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        await consumer.handle_event("learning.session.completed", payload)

        # Verify metadata contains all expected fields
        call_args = mock_service.record_metric.call_args
        metadata = call_args[1]["metadata"]
        assert metadata["session_id"] == str(session_id)
        assert metadata["topic"] == "Advanced React"
        assert metadata["duration_minutes"] == 60
