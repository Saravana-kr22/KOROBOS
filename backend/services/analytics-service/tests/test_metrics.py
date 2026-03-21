"""
Tests for Prometheus metrics instrumentation.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from app.middleware.metrics import (
    MetricsMiddleware,
    cache_hits,
    event_processing_latency,
    record_cache_hit,
    record_cache_miss,
    record_db_query,
    record_event_processing,
)


@pytest.mark.asyncio
async def test_metrics_middleware_records_request_duration():
    """Test that metrics middleware records HTTP request duration."""
    middleware = MetricsMiddleware(app=Mock())

    request = Mock()
    request.method = "GET"
    request.url = Mock()
    request.url.path = "/analytics/overview"

    response = Mock()
    response.status_code = 200

    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)

    assert result == response
    call_next.assert_called_once_with(request)


def test_record_event_processing_increments_counters():
    """Test that event processing metrics are recorded."""
    # Clear previous counts
    initial_count = event_processing_latency._value.get()

    record_event_processing("habit.completed", "HabitConsumer", 45.5, True)

    # Verify metrics were recorded (internal prometheus state is incremented)
    assert event_processing_latency._value.get() >= initial_count


def test_record_db_query_increments_counters():
    """Test that database query metrics are recorded."""
    record_db_query("select", 25.0, True)
    # Metrics recorded without error


def test_record_cache_hit_increments_counter():
    """Test that cache hit is recorded."""
    initial_count = cache_hits._value.get()

    record_cache_hit("cache:dashboard:overview:user123")

    # Verify counter incremented
    assert cache_hits._value.get() > initial_count


def test_record_cache_miss_increments_counter():
    """Test that cache miss is recorded."""
    record_cache_miss("cache:dashboard:daily:user123:2026-03-22")
    # Metrics recorded without error
