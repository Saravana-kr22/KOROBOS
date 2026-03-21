"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Integration tests for analytics service — event consumer and metric recording.
"""

import importlib
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from backend.shared.database.base_model import Base

# Populated dynamically by the _setup_analytics_service_imports fixture.
# Declared here so static analysers (ruff F821, mypy) recognise the name.
LearningEventConsumer: Any = None


@pytest.fixture(scope="function")
def _setup_analytics_service_imports():
    """Set up imports for analytics service with proper module isolation."""
    # Ensure analytics-service path is in sys.path for imports
    _test_dir = Path(__file__).resolve().parent
    _backend_root = _test_dir.parent
    _service_path = str(_backend_root / "services" / "analytics-service")

    # Store original sys.path and modules
    _original_sys_path = sys.path.copy()

    # Remove all service paths to force fresh import from analytics-service
    _to_remove_paths = [
        str(_backend_root / "services" / "habit-service"),
        str(_backend_root / "services" / "learning-service"),
        _service_path,
    ]
    for path in _to_remove_paths:
        if path in sys.path:
            sys.path.remove(path)

    # Add analytics-service path at front
    sys.path.insert(0, _service_path)

    # Clear app.* modules that might have been cached from other services
    _to_remove = [k for k in sys.modules.copy() if k.startswith("app")]
    for mod in _to_remove:
        del sys.modules[mod]

    # Clear SQLAlchemy registry to avoid table redefinition errors
    # This removes any previously registered models from other services
    Base.registry._class_registry.clear()
    Base.metadata.clear()

    # Import fresh for this test
    _learning_consumer_module = importlib.import_module("app.events.learning_consumer")
    globals()["LearningEventConsumer"] = _learning_consumer_module.LearningEventConsumer
    yield
    # Cleanup after test - restore original sys.path and clear app modules
    sys.path[:] = _original_sys_path
    _to_remove = [k for k in sys.modules.copy() if k.startswith("app")]
    for mod in _to_remove:
        del sys.modules[mod]
    # Also clear SQLAlchemy registry for next test
    Base.registry._class_registry.clear()
    Base.metadata.clear()


@pytest.mark.anyio
async def test_learning_consumer_records_metric_on_session_completed(
    _setup_analytics_service_imports,
):
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

    with (
        patch(
            "app.events.learning_consumer.async_session_factory"
        ) as mock_session_factory,
        patch("app.events.learning_consumer.AnalyticsService") as mock_service_class,
    ):
        # Setup mock session
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        # Setup mock service
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        # Create consumer instance and call handler
        consumer = LearningEventConsumer(
            topics=["learning.session.completed", "learning.session.logged"],
            group_id="analytics-service-learning",
        )
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
async def test_learning_consumer_records_metric_on_session_logged(
    _setup_analytics_service_imports,
):
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

    consumer = LearningEventConsumer(
        topics=["learning.session.completed", "learning.session.logged"],
        group_id="analytics-service-learning",
    )

    with (
        patch(
            "app.events.learning_consumer.async_session_factory"
        ) as mock_session_factory,
        patch("app.events.learning_consumer.AnalyticsService") as mock_service_class,
    ):
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        await consumer.handle_event("learning.session.logged", payload)

        mock_service.record_metric.assert_called_once()
        call_args = mock_service.record_metric.call_args
        assert call_args[1]["metric_type"] == "learning_hours"
        assert call_args[1]["value"] == pytest.approx(duration_minutes / 60.0, abs=0.01)


@pytest.mark.anyio
async def test_learning_consumer_handles_missing_user_id_gracefully(
    _setup_analytics_service_imports,
):
    """Test that consumer skips event gracefully when user_id is missing."""
    payload = {
        "session_id": str(uuid4()),
        "topic": "Some Topic",
        "duration": 30,
    }

    consumer = LearningEventConsumer(
        topics=["learning.session.completed", "learning.session.logged"],
        group_id="analytics-service-learning",
    )

    with patch(
        "app.events.learning_consumer.async_session_factory"
    ) as mock_session_factory:
        # Should not raise, should return early
        await consumer.handle_event("learning.session.completed", payload)
        # SessionLocal should not be called
        mock_session_factory.assert_not_called()


@pytest.mark.anyio
async def test_learning_consumer_handles_missing_duration_gracefully(
    _setup_analytics_service_imports,
):
    """Test that consumer skips event gracefully when duration is missing."""
    payload = {
        "session_id": str(uuid4()),
        "user_id": str(uuid4()),
        "topic": "Some Topic",
    }

    consumer = LearningEventConsumer(
        topics=["learning.session.completed", "learning.session.logged"],
        group_id="analytics-service-learning",
    )

    with patch(
        "app.events.learning_consumer.async_session_factory"
    ) as mock_session_factory:
        # Should not raise, should return early
        await consumer.handle_event("learning.session.completed", payload)
        # SessionLocal should not be called
        mock_session_factory.assert_not_called()


@pytest.mark.anyio
async def test_learning_consumer_handles_invalid_user_id_format(
    _setup_analytics_service_imports,
):
    """Test that consumer handles invalid UUID format in user_id."""
    payload = {
        "session_id": str(uuid4()),
        "user_id": "not-a-uuid",
        "topic": "Some Topic",
        "duration": 30,
    }

    consumer = LearningEventConsumer(
        topics=["learning.session.completed", "learning.session.logged"],
        group_id="analytics-service-learning",
    )

    with patch("app.events.learning_consumer.async_session_factory"):
        # Should not raise, should handle gracefully
        await consumer.handle_event("learning.session.completed", payload)


@pytest.mark.anyio
async def test_learning_consumer_persists_metadata(
    _setup_analytics_service_imports,
):
    """Test that consumer includes comprehensive metadata in recorded metric."""
    user_id = uuid4()
    session_id = uuid4()
    payload = {
        "session_id": str(session_id),
        "user_id": str(user_id),
        "topic": "Advanced React",
        "duration": 60,
    }

    consumer = LearningEventConsumer(
        topics=["learning.session.completed", "learning.session.logged"],
        group_id="analytics-service-learning",
    )

    with (
        patch(
            "app.events.learning_consumer.async_session_factory"
        ) as mock_session_factory,
        patch("app.events.learning_consumer.AnalyticsService") as mock_service_class,
    ):
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        await consumer.handle_event("learning.session.completed", payload)

        # Verify metadata contains all expected fields
        call_args = mock_service.record_metric.call_args
        metadata = call_args[1]["metadata"]
        assert metadata["session_id"] == str(session_id)
        assert metadata["topic"] == "Advanced React"
        assert metadata["duration_minutes"] == 60
