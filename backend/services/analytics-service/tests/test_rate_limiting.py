"""
Tests for rate limiting middleware.
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
import redis
from app.middleware.rate_limiter import RedisRateLimiter, rate_limit_middleware


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return Mock(spec=redis.Redis)


@pytest.fixture
def rate_limiter(mock_redis):
    """Rate limiter instance with mocked Redis."""
    return RedisRateLimiter(mock_redis, requests_per_minute=100)


@pytest.mark.asyncio
async def test_rate_limiter_allows_request_within_limit(rate_limiter, mock_redis):
    """Test that requests within limit are allowed."""
    mock_redis.zremrangebyscore.return_value = None
    mock_redis.zcard.return_value = 50
    mock_redis.zadd.return_value = 1
    mock_redis.expire.return_value = 1

    allowed, info = await rate_limiter.check_rate_limit("user123")

    assert allowed is True
    assert info["remaining"] == 49
    assert info["limit"] == 100


@pytest.mark.asyncio
async def test_rate_limiter_rejects_request_over_limit(rate_limiter, mock_redis):
    """Test that requests over limit are rejected."""
    mock_redis.zremrangebyscore.return_value = None
    mock_redis.zcard.return_value = 100
    mock_redis.zrange.return_value = [(f"req_{i}", 1000000) for i in range(100)]

    allowed, info = await rate_limiter.check_rate_limit("user123")

    assert allowed is False
    assert info["remaining"] == 0
    assert info["limit"] == 100


@pytest.mark.asyncio
async def test_rate_limiter_handles_missing_user_id(rate_limiter):
    """Test that missing user_id allows request."""
    allowed, info = await rate_limiter.check_rate_limit("")

    assert allowed is True
    assert info is None


@pytest.mark.asyncio
async def test_rate_limiter_handles_redis_failure(rate_limiter, mock_redis):
    """Test that Redis failures allow request (fail open)."""
    mock_redis.zremrangebyscore.side_effect = redis.RedisError("Connection error")

    allowed, info = await rate_limiter.check_rate_limit("user123")

    assert allowed is True
    assert info is None


@pytest.mark.asyncio
async def test_rate_limit_middleware_allows_under_limit():
    """Test middleware allows requests under limit."""
    app = Mock()
    app.state = Mock()

    mock_limiter = Mock(spec=RedisRateLimiter)
    mock_limiter.check_rate_limit = AsyncMock(
        return_value=(True, {"limit": 100, "remaining": 99, "reset_in_seconds": 60})
    )
    app.state.rate_limiter = mock_limiter

    request = Mock(spec=Mock)
    request.app = app
    request.headers = {"X-User-ID": "user123"}

    call_next = AsyncMock(return_value=MagicMock())

    response = await rate_limit_middleware(request, call_next)

    assert response is not None
    call_next.assert_called_once_with(request)


@pytest.mark.asyncio
async def test_rate_limit_middleware_rejects_over_limit():
    """Test middleware rejects requests over limit."""
    app = Mock()
    app.state = Mock()

    mock_limiter = Mock(spec=RedisRateLimiter)
    mock_limiter.check_rate_limit = AsyncMock(
        return_value=(
            False,
            {"limit": 100, "remaining": 0, "reset_in_seconds": 45},
        )
    )
    app.state.rate_limiter = mock_limiter

    request = Mock(spec=Mock)
    request.app = app
    request.headers = {"X-User-ID": "user123"}

    response = await rate_limit_middleware(request, None)

    assert response.status_code == 429
