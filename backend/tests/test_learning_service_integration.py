"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Integration tests for the Learning Service API.

Tests the full HTTP contract using httpx + FastAPI's TestClient.
Mocks external dependencies (Kafka, Redis, DB) so the tests run in CI
without infrastructure.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import configure_mappers

from backend.shared.database.base_model import Base

# ── path setup ──────────────────────────────────────────────────────────────
_test_dir = Path(__file__).resolve().parent
_backend_root = _test_dir.parent
_service_path = str(_backend_root / "services" / "learning-service")

if _service_path in sys.path:
    sys.path.remove(_service_path)
sys.path.insert(0, _service_path)

# Clear any cached app modules ONLY IF they are from a different service
# to avoid SQLAlchemy "Table already defined" errors when multiple test files
# import from the same service.
_current_app_path = ""
if "app" in sys.modules:
    _app_mod = sys.modules["app"]
    _current_app_path = getattr(_app_mod, "__file__", "") or ""

if "learning-service" not in _current_app_path:
    # Clear app modules that might have been cached from other services
    _to_remove = [k for k in sys.modules if k.startswith("app")]
    for mod in _to_remove:
        del sys.modules[mod]

    # Clear SQLAlchemy registry to avoid table redefinition errors
    # and registry pollution across service tests in CI.
    Base.registry._class_registry.clear()
    Base.metadata.clear()

# ── app import (after path is set) ──────────────────────────────────────────
from httpx import ASGITransport, AsyncClient  # noqa: E402

# Patch infrastructure before importing the app
with patch("backend.shared.messaging.producer.get_producer", new=AsyncMock()):
    import importlib

    app_module = importlib.import_module("app.main")
    app = app_module.app

# Configure mappers to catch relationship resolution issues before tests run.
try:
    configure_mappers()
except Exception as e:
    msg = f"ERROR: SQLAlchemy mapper configuration failed: {e}"
    print(msg)
    # Fail early if mapper configuration has serious issues
    raise

# ── helpers ─────────────────────────────────────────────────────────────────
USER_ID = str(uuid4())
AUTH_HEADERS = {"X-User-ID": USER_ID}


def _session_payload(
    topic: str = "Python", duration: int = 30, notes: str = ""
) -> dict:
    return {"topic": topic, "duration": duration, "notes": notes}


def _make_db_session_mock(sessions=None, total=0, stats=None):
    """Return a mock AsyncSession that satisfies learning-service queries."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = total
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = sessions or []
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()
    mock_db.delete = AsyncMock()
    mock_db.add = MagicMock()
    return mock_db


# ── fixtures ────────────────────────────────────────────────────────────────
@pytest.fixture
async def client():
    """AsyncClient wired to the learning-service ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── health / root ────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
    assert resp.json()["service"] == "learning-service"


@pytest.mark.anyio
async def test_metrics_endpoint_returns_prometheus_text(client: AsyncClient):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]


@pytest.mark.anyio
async def test_root_endpoint(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "learning-service"


# ── missing auth header ──────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_sessions_requires_user_id_header(client: AsyncClient):
    """Endpoints should return 422 when X-User-ID header is missing."""
    resp = await client.get("/sessions")
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_stats_requires_user_id_header(client: AsyncClient):
    resp = await client.get("/stats")
    assert resp.status_code == 422


# ── POST /sessions (manual log) ──────────────────────────────────────────────


@pytest.mark.anyio
async def test_log_session_returns_201(client: AsyncClient):
    from datetime import datetime, timezone

    from app.models.session_model import LearningSession

    now = datetime.now(timezone.utc)
    fake_session = MagicMock(spec=LearningSession)
    fake_session.id = uuid4()
    fake_session.user_id = USER_ID
    fake_session.topic = "Python"
    fake_session.topic_id = None
    fake_session.duration = 30
    fake_session.notes = None
    fake_session.status = "completed"
    fake_session.start_time = None
    fake_session.end_time = None
    fake_session.created_at = now
    fake_session.updated_at = now
    fake_session.session_notes = []
    fake_session.topic_rel = None

    mock_db = _make_db_session_mock()
    mock_db.add = MagicMock()

    async def fake_flush():
        pass

    mock_db.flush = AsyncMock(side_effect=fake_flush)

    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.repository.LearningRepository.create",
            new=AsyncMock(return_value=fake_session),
        ),
        patch("backend.shared.messaging.producer.publish_event", new=AsyncMock()),
    ):
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post(
            "/sessions",
            json=_session_payload(),
            headers=AUTH_HEADERS,
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["topic"] == "Python"
    assert data["duration"] == 30
    assert data["status"] == "completed"


@pytest.mark.anyio
async def test_log_session_validates_duration(client: AsyncClient):
    """Duration must be > 0."""
    with patch("backend.shared.database.connection.get_db_session"):
        resp = await client.post(
            "/sessions",
            json={"topic": "Python", "duration": 0},
            headers=AUTH_HEADERS,
        )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_log_session_validates_topic(client: AsyncClient):
    """Topic must not be empty."""
    with patch("backend.shared.database.connection.get_db_session"):
        resp = await client.post(
            "/sessions",
            json={"topic": "", "duration": 30},
            headers=AUTH_HEADERS,
        )
    assert resp.status_code == 422


# ── GET /sessions ─────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_list_sessions_returns_200(client: AsyncClient):
    mock_db = _make_db_session_mock(sessions=[], total=0)

    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.repository.LearningRepository.list_by_user",
            new=AsyncMock(return_value=([], 0)),
        ),
    ):
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.get("/sessions", headers=AUTH_HEADERS)

    assert resp.status_code == 200
    data = resp.json()
    assert "sessions" in data
    assert "total" in data
    assert data["total"] == 0


@pytest.mark.anyio
async def test_list_sessions_pagination_params(client: AsyncClient):
    """offset and limit query params must be accepted."""
    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.repository.LearningRepository.list_by_user",
            new=AsyncMock(return_value=([], 0)),
        ),
    ):
        mock_get_db.return_value.__aenter__ = AsyncMock(
            return_value=_make_db_session_mock()
        )
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.get("/sessions?offset=10&limit=5", headers=AUTH_HEADERS)

    assert resp.status_code == 200


# ── GET /stats ────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_get_stats_returns_all_fields(client: AsyncClient):
    fake_stats = {
        "total_sessions": 5,
        "total_minutes": 150,
        "topics": ["Python", "ML"],
        "sessions_today": 1,
        "current_streak": 3,
        "weekly_minutes": 90,
        "topic_distribution": {"Python": 90, "ML": 60},
    }

    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.repository.LearningRepository.get_stats",
            new=AsyncMock(return_value=fake_stats),
        ),
    ):
        mock_get_db.return_value.__aenter__ = AsyncMock(
            return_value=_make_db_session_mock()
        )
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.get("/stats", headers=AUTH_HEADERS)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 5
    assert data["current_streak"] == 3
    assert data["weekly_minutes"] == 90
    assert "topic_distribution" in data


# ── POST /topics ──────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_create_topic_returns_201(client: AsyncClient):
    from datetime import datetime, timezone

    from app.models.topic_model import Topic

    now = datetime.now(timezone.utc)
    fake_topic = MagicMock(spec=Topic)
    fake_topic.id = uuid4()
    fake_topic.user_id = USER_ID
    fake_topic.name = "Deep Learning"
    fake_topic.created_at = now
    fake_topic.updated_at = now
    fake_topic.sessions = []

    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.topic_repository.TopicRepository.create",
            new=AsyncMock(return_value=fake_topic),
        ),
        patch("backend.shared.messaging.producer.publish_event", new=AsyncMock()),
    ):
        mock_get_db.return_value.__aenter__ = AsyncMock(
            return_value=_make_db_session_mock()
        )
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post(
            "/topics",
            json={"name": "Deep Learning"},
            headers=AUTH_HEADERS,
        )

    assert resp.status_code == 201
    assert resp.json()["name"] == "Deep Learning"


@pytest.mark.anyio
async def test_create_topic_validates_name(client: AsyncClient):
    """Empty topic name should fail validation."""
    with patch("backend.shared.database.connection.get_db_session"):
        resp = await client.post(
            "/topics",
            json={"name": ""},
            headers=AUTH_HEADERS,
        )
    assert resp.status_code == 422


# ── GET /topics ───────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_list_topics_returns_200(client: AsyncClient):
    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.topic_repository.TopicRepository.list_by_user",
            new=AsyncMock(return_value=([], 0)),
        ),
    ):
        mock_get_db.return_value.__aenter__ = AsyncMock(
            return_value=_make_db_session_mock()
        )
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.get("/topics", headers=AUTH_HEADERS)

    assert resp.status_code == 200
    data = resp.json()
    assert "topics" in data
    assert "total" in data


# ── Timer — session/start ─────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_start_session_returns_409_when_already_active(client: AsyncClient):
    from app.models.session_model import LearningSession

    existing = MagicMock(spec=LearningSession)
    existing.id = uuid4()
    existing.status = "active"

    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.repository.LearningRepository.get_active_session",
            new=AsyncMock(return_value=existing),
        ),
    ):
        mock_get_db.return_value.__aenter__ = AsyncMock(
            return_value=_make_db_session_mock()
        )
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post(
            "/session/start",
            json={"topic": "Python"},
            headers=AUTH_HEADERS,
        )

    assert resp.status_code == 409
    assert resp.json()["detail"]["error"] == "SESSION_ALREADY_ACTIVE"


# ── Rate limiting ─────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_rate_limit_returns_429_when_exceeded(client: AsyncClient):
    """Simulate Redis reporting count > 30 → expect 429."""
    from datetime import datetime, timezone

    from app.models.session_model import LearningSession

    now = datetime.now(timezone.utc)
    fake_session = MagicMock(spec=LearningSession)
    fake_session.id = uuid4()
    fake_session.user_id = USER_ID
    fake_session.topic = "Python"
    fake_session.topic_id = None
    fake_session.duration = 30
    fake_session.notes = None
    fake_session.status = "completed"
    fake_session.start_time = None
    fake_session.end_time = None
    fake_session.created_at = now
    fake_session.updated_at = now
    fake_session.session_notes = []
    fake_session.topic_rel = None

    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=31)  # Over the limit
    mock_redis.expire = AsyncMock()

    app.state.redis = mock_redis

    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.repository.LearningRepository.create",
            new=AsyncMock(return_value=fake_session),
        ),
        patch("backend.shared.messaging.producer.publish_event", new=AsyncMock()),
    ):
        mock_get_db.return_value.__aenter__ = AsyncMock(
            return_value=_make_db_session_mock()
        )
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.post(
            "/sessions",
            json=_session_payload(),
            headers=AUTH_HEADERS,
        )

    app.state.redis = None  # clean up
    assert resp.status_code == 429
    assert resp.json()["detail"]["error"] == "RATE_LIMIT_EXCEEDED"


# ── GET /sessions/{id} — ownership ───────────────────────────────────────────


@pytest.mark.anyio
async def test_get_session_returns_404_for_wrong_user(client: AsyncClient):
    from app.models.session_model import LearningSession

    other_user = uuid4()
    fake_session = MagicMock(spec=LearningSession)
    fake_session.id = uuid4()
    fake_session.user_id = other_user  # different user

    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.repository.LearningRepository.get_by_id",
            new=AsyncMock(return_value=fake_session),
        ),
    ):
        mock_get_db.return_value.__aenter__ = AsyncMock(
            return_value=_make_db_session_mock()
        )
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.get(
            f"/sessions/{uuid4()}",
            headers=AUTH_HEADERS,
        )

    assert resp.status_code == 404


# ── DELETE /sessions/{id} ─────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_delete_session_returns_204(client: AsyncClient):
    from app.models.session_model import LearningSession

    session_id = uuid4()
    fake_session = MagicMock(spec=LearningSession)
    fake_session.id = session_id
    fake_session.user_id = UUID(
        USER_ID
    )  # Must be UUID to match route's _get_user_id return type

    with (
        patch("backend.shared.database.connection.get_db_session") as mock_get_db,
        patch(
            "app.repositories.repository.LearningRepository.get_by_id",
            new=AsyncMock(return_value=fake_session),
        ),
        patch(
            "app.repositories.repository.LearningRepository.delete",
            new=AsyncMock(),
        ),
    ):
        mock_db = _make_db_session_mock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await client.delete(
            f"/sessions/{session_id}",
            headers=AUTH_HEADERS,
        )

    assert resp.status_code == 204
