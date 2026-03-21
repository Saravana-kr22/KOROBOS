"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for the Learning Service — timer, topics, analytics, events.
"""

import importlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import configure_mappers

# Ensure learning-service path is in sys.path for imports
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

# RE-ADDED: Namespace collision with analytics-service requires clearing "app"
# but only if switching services to avoid metadata conflicts.

# Import service modules
LearningSession = importlib.import_module("app.models.model").LearningSession  # type: ignore[assignment]
Topic = importlib.import_module("app.models.model").Topic  # type: ignore[assignment]
SessionNote = importlib.import_module("app.models.model").SessionNote

LearningRepository = importlib.import_module(
    "app.repositories.repository"
).LearningRepository
TopicRepository = importlib.import_module(
    "app.repositories.topic_repository"
).TopicRepository

LearningSessionCreate = importlib.import_module(
    "app.schemas.schema"
).LearningSessionCreate
SessionStartRequest = importlib.import_module("app.schemas.schema").SessionStartRequest
SessionStopRequest = importlib.import_module("app.schemas.schema").SessionStopRequest
SessionPauseRequest = importlib.import_module("app.schemas.schema").SessionPauseRequest
SessionResumeRequest = importlib.import_module(
    "app.schemas.schema"
).SessionResumeRequest
TopicCreate = importlib.import_module("app.schemas.schema").TopicCreate

LearningSessionLoggedEvent = importlib.import_module(
    "app.events.events"
).LearningSessionLoggedEvent
LearningSessionStartedEvent = importlib.import_module(
    "app.events.events"
).LearningSessionStartedEvent
LearningSessionCompletedEvent = importlib.import_module(
    "app.events.events"
).LearningSessionCompletedEvent
LearningTopicCreatedEvent = importlib.import_module(
    "app.events.events"
).LearningTopicCreatedEvent

TimerService = importlib.import_module("app.services.timer_service").TimerService
LearningService = importlib.import_module("app.services.service_logic").LearningService

# Configure mappers to catch relationship resolution issues before tests run.
try:
    configure_mappers()
except Exception as e:
    msg = f"ERROR: SQLAlchemy mapper configuration failed: {e}"
    print(msg)
    # Fail early if mapper configuration has serious issues
    raise


def _utcnow():
    return datetime.now(timezone.utc)


def make_session(**kwargs) -> "LearningSession":  # type: ignore[valid-type]
    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        topic="Python",
        topic_id=None,
        duration=0,
        notes=None,
        status="completed",
        start_time=None,
        end_time=None,
        created_at=_utcnow(),
        updated_at=_utcnow(),
        session_notes=[],
        topic_rel=None,
    )
    defaults.update(kwargs)
    obj = MagicMock(spec=LearningSession)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def make_topic(**kwargs) -> "Topic":  # type: ignore[valid-type]
    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        name="Machine Learning",
        created_at=_utcnow(),
        updated_at=_utcnow(),
        sessions=[],
    )
    defaults.update(kwargs)
    obj = MagicMock(spec=Topic)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ===========================================================================
# Event schema tests
# ===========================================================================


def test_session_logged_event_type():
    event = LearningSessionLoggedEvent(
        payload={"session_id": str(uuid4()), "topic": "ML", "duration": 30}
    )
    assert event.event_type == "learning.session.logged"
    assert event.source_service == "learning-service"


def test_session_started_event_type():
    event = LearningSessionStartedEvent(
        payload={"session_id": str(uuid4()), "topic": "ML"}
    )
    assert event.event_type == "learning.session.started"


def test_session_completed_event_type():
    event = LearningSessionCompletedEvent(
        payload={"session_id": str(uuid4()), "duration": 45}
    )
    assert event.event_type == "learning.session.completed"


def test_topic_created_event_type():
    event = LearningTopicCreatedEvent(
        payload={"topic_id": str(uuid4()), "name": "Python"}
    )
    assert event.event_type == "learning.topic.created"


def test_event_has_auto_event_id():
    event = LearningSessionLoggedEvent(payload={})
    assert event.event_id is not None
    assert len(event.event_id) > 0


# ===========================================================================
# Repository: pause / resume / stop mechanics
# ===========================================================================


@pytest.mark.anyio
async def test_pause_accumulates_duration():
    """Pausing a session should accumulate elapsed minutes into duration."""
    session = MagicMock(spec=LearningSession)
    session.status = "active"
    session.duration = 10  # already accumulated 10 min
    session.start_time = _utcnow() - timedelta(minutes=5)  # 5 min since resume

    db_session = AsyncMock()
    repo = LearningRepository(db_session)
    result = await repo.pause_session(session)

    assert result.status == "paused"
    assert result.start_time is None
    # Should have added ~5 min (int(5.0)) to the existing 10
    assert result.duration >= 15


@pytest.mark.anyio
async def test_stop_session_computes_duration():
    """Stopping a session should compute total elapsed time."""
    session = MagicMock(spec=LearningSession)
    session.status = "active"
    session.duration = 0
    session.start_time = _utcnow() - timedelta(minutes=30)

    db_session = AsyncMock()
    repo = LearningRepository(db_session)
    result = await repo.stop_session(session)

    assert result.status == "completed"
    assert result.end_time is not None
    assert result.duration >= 30  # at least 30 min


@pytest.mark.anyio
async def test_resume_session_sets_start_time():
    """Resuming a paused session should set a new start_time."""
    session = MagicMock(spec=LearningSession)
    session.status = "paused"
    session.start_time = None
    session.duration = 15

    db_session = AsyncMock()
    repo = LearningRepository(db_session)
    result = await repo.resume_session(session)

    assert result.status == "active"
    assert result.start_time is not None


# ===========================================================================
# Timer Service: conflict detection
# ===========================================================================


@pytest.mark.anyio
async def test_start_session_raises_409_if_active_exists():
    """Starting a session when one is already active must raise 409."""
    from fastapi import HTTPException

    user_id = uuid4()
    db_session = AsyncMock()

    active = make_session(status="active", user_id=user_id)

    svc = TimerService(db_session)
    svc.repo = AsyncMock()
    svc.repo.get_active_session = AsyncMock(return_value=active)

    with pytest.raises(HTTPException) as exc_info:
        await svc.start_session(user_id, SessionStartRequest(topic="Python"))

    assert exc_info.value.status_code == 409


@pytest.mark.anyio
async def test_stop_session_raises_404_for_wrong_user():
    """Stopping a session belonging to another user must raise 404."""
    from fastapi import HTTPException

    user_id = uuid4()
    other_user_id = uuid4()
    session_id = uuid4()

    db_session = AsyncMock()
    svc = TimerService(db_session)
    svc.repo = AsyncMock()
    svc.repo.get_by_id = AsyncMock(
        return_value=make_session(id=session_id, user_id=other_user_id, status="active")
    )

    with pytest.raises(HTTPException) as exc_info:
        await svc.stop_session(user_id, SessionStopRequest(session_id=session_id))

    assert exc_info.value.status_code == 404


@pytest.mark.anyio
async def test_pause_raises_400_if_not_active():
    """Pausing a completed session must raise 400."""
    from fastapi import HTTPException

    user_id = uuid4()
    session_id = uuid4()

    db_session = AsyncMock()
    svc = TimerService(db_session)
    svc.repo = AsyncMock()
    svc.repo.get_by_id = AsyncMock(
        return_value=make_session(id=session_id, user_id=user_id, status="completed")
    )

    with pytest.raises(HTTPException) as exc_info:
        await svc.pause_session(user_id, SessionPauseRequest(session_id=session_id))

    assert exc_info.value.status_code == 400


@pytest.mark.anyio
async def test_resume_raises_400_if_not_paused():
    """Resuming an active session must raise 400."""
    from fastapi import HTTPException

    user_id = uuid4()
    session_id = uuid4()

    db_session = AsyncMock()
    svc = TimerService(db_session)
    svc.repo = AsyncMock()
    svc.repo.get_by_id = AsyncMock(
        return_value=make_session(id=session_id, user_id=user_id, status="active")
    )

    with pytest.raises(HTTPException) as exc_info:
        await svc.resume_session(user_id, SessionResumeRequest(session_id=session_id))

    assert exc_info.value.status_code == 400


# ===========================================================================
# Topic management
# ===========================================================================


@pytest.mark.anyio
async def test_create_topic_publishes_event():
    """Creating a topic should publish LearningTopicCreatedEvent."""
    user_id = uuid4()
    topic = make_topic(user_id=user_id, name="Deep Learning")

    db_session = AsyncMock()
    svc = LearningService(db_session)
    svc.topic_repo = AsyncMock()
    svc.topic_repo.create = AsyncMock(return_value=topic)

    with patch(
        "app.services.service_logic.publish_event", new=AsyncMock()
    ) as mock_publish:
        result = await svc.create_topic(user_id, TopicCreate(name="Deep Learning"))

    assert result.name == "Deep Learning"
    mock_publish.assert_called_once()
    event_arg = mock_publish.call_args[0][0]
    assert isinstance(event_arg, LearningTopicCreatedEvent)
    assert event_arg.payload["name"] == "Deep Learning"


@pytest.mark.anyio
async def test_delete_topic():
    """Deleting a topic should call topic_repo.delete."""
    topic = make_topic()

    db_session = AsyncMock()
    svc = LearningService(db_session)
    svc.topic_repo = AsyncMock()
    svc.topic_repo.delete = AsyncMock()

    await svc.delete_topic(topic)
    svc.topic_repo.delete.assert_called_once_with(topic)


# ===========================================================================
# Analytics: streak calculation
# ===========================================================================


@pytest.mark.anyio
async def test_streak_zero_with_no_sessions():
    """No sessions → streak = 0."""
    user_id = uuid4()
    today = _utcnow().date()

    db_session = AsyncMock()
    repo = LearningRepository(db_session)

    # Simulate empty result from DB
    mock_result = MagicMock()
    mock_result.all.return_value = []
    db_session.execute = AsyncMock(return_value=mock_result)

    streak = await repo._calculate_streak(user_id, today)
    assert streak == 0


@pytest.mark.anyio
async def test_streak_consecutive_days():
    """Sessions on 3 consecutive days → streak = 3."""
    user_id = uuid4()
    today = _utcnow().date()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    db_session = AsyncMock()
    repo = LearningRepository(db_session)

    # Simulate 3 days of results
    rows = [MagicMock(day=today), MagicMock(day=yesterday), MagicMock(day=two_days_ago)]
    mock_result = MagicMock()
    mock_result.all.return_value = rows
    db_session.execute = AsyncMock(return_value=mock_result)

    streak = await repo._calculate_streak(user_id, today)
    assert streak == 3


@pytest.mark.anyio
async def test_streak_breaks_on_gap():
    """Gap in days → streak only counts from today to gap."""
    user_id = uuid4()
    today = _utcnow().date()
    yesterday = today - timedelta(days=1)
    three_days_ago = today - timedelta(days=3)  # gap on day 2

    db_session = AsyncMock()
    repo = LearningRepository(db_session)

    rows = [
        MagicMock(day=today),
        MagicMock(day=yesterday),
        MagicMock(day=three_days_ago),
    ]
    mock_result = MagicMock()
    mock_result.all.return_value = rows
    db_session.execute = AsyncMock(return_value=mock_result)

    streak = await repo._calculate_streak(user_id, today)
    assert streak == 2  # today + yesterday only


# ===========================================================================
# Session log — manual
# ===========================================================================


@pytest.mark.anyio
async def test_log_session_publishes_event():
    """Manually logging a session should publish LearningSessionLoggedEvent."""
    user_id = uuid4()
    session = make_session(user_id=user_id, topic="ML", duration=60, status="completed")

    db_session = AsyncMock()
    svc = LearningService(db_session)
    svc.repo = AsyncMock()
    svc.repo.create = AsyncMock(return_value=session)
    svc.topic_repo = AsyncMock()

    with patch(
        "app.services.service_logic.publish_event", new=AsyncMock()
    ) as mock_publish:
        result = await svc.log_session(
            user_id, LearningSessionCreate(topic="ML", duration=60)
        )

    assert result.topic == "ML"
    mock_publish.assert_called_once()
    event_arg = mock_publish.call_args[0][0]
    assert isinstance(event_arg, LearningSessionLoggedEvent)
    assert event_arg.payload["duration"] == 60


@pytest.mark.anyio
async def test_log_session_status_is_completed():
    """A manually logged session must have status=completed."""
    user_id = uuid4()
    session = make_session(user_id=user_id, status="completed")

    db_session = AsyncMock()
    svc = LearningService(db_session)
    svc.repo = AsyncMock()
    svc.repo.create = AsyncMock(return_value=session)

    with patch("app.services.service_logic.publish_event", new=AsyncMock()):
        result = await svc.log_session(
            user_id, LearningSessionCreate(topic="Python", duration=45)
        )

    assert result.status == "completed"


# ===========================================================================
# Note linking
# ===========================================================================


@pytest.mark.anyio
async def test_link_note_calls_repo():
    """link_note should delegate to repo.link_note."""
    session_id = uuid4()
    note_id = uuid4()

    db_session = AsyncMock()
    svc = LearningService(db_session)
    svc.repo = AsyncMock()
    svc.repo.link_note = AsyncMock()

    await svc.link_note(session_id, note_id)
    svc.repo.link_note.assert_called_once_with(session_id, note_id)


@pytest.mark.anyio
async def test_unlink_note_calls_repo():
    """unlink_note should delegate to repo.unlink_note."""
    session_id = uuid4()
    note_id = uuid4()

    db_session = AsyncMock()
    svc = LearningService(db_session)
    svc.repo = AsyncMock()
    svc.repo.unlink_note = AsyncMock()

    await svc.unlink_note(session_id, note_id)
    svc.repo.unlink_note.assert_called_once_with(session_id, note_id)


# ===========================================================================
# Analytics: streak — yesterday-only edge case (Sprint 9 regression)
# ===========================================================================


@pytest.mark.anyio
async def test_streak_yesterday_no_session_today():
    """No session today but session yesterday → streak = 1, not 0."""
    user_id = uuid4()
    today = _utcnow().date()
    yesterday = today - timedelta(days=1)

    db_session = AsyncMock()
    repo = LearningRepository(db_session)

    rows = [MagicMock(day=yesterday)]
    mock_result = MagicMock()
    mock_result.all.return_value = rows
    db_session.execute = AsyncMock(return_value=mock_result)

    streak = await repo._calculate_streak(user_id, today)
    assert streak == 1


@pytest.mark.anyio
async def test_streak_yesterday_and_day_before():
    """Sessions on yesterday and day-before-yesterday, none today → streak = 2."""
    user_id = uuid4()
    today = _utcnow().date()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    db_session = AsyncMock()
    repo = LearningRepository(db_session)

    rows = [MagicMock(day=yesterday), MagicMock(day=two_days_ago)]
    mock_result = MagicMock()
    mock_result.all.return_value = rows
    db_session.execute = AsyncMock(return_value=mock_result)

    streak = await repo._calculate_streak(user_id, today)
    assert streak == 2


# ===========================================================================
# Timer: pause → immediate stop produces zero duration without crashing
# ===========================================================================


@pytest.mark.anyio
async def test_stop_after_immediate_pause_zero_duration():
    """Pausing then immediately stopping a session with 0 accumulated time
    should not crash and should produce duration = 0."""
    session = MagicMock(spec=LearningSession)
    session.status = "paused"
    session.duration = 0
    session.start_time = None  # cleared by pause

    db_session = AsyncMock()
    repo = LearningRepository(db_session)
    result = await repo.stop_session(session)

    assert result.status == "completed"
    assert result.end_time is not None
    assert result.duration == 0  # no elapsed time was added
