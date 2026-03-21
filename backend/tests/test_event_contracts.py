"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Contract tests for the Kafka event catalog.
"""

import json
from pathlib import Path

import pytest

from backend.shared.messaging.schema_registry import validate_event
from backend.shared.messaging.schemas import BaseEvent

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "events"

EVENT_SAMPLES = {
    "note.created": {
        "note_id": "note-123",
        "user_id": "user-123",
        "title": "Deep Work",
        "content_md": "Focus blocks and task list",
        "tags": ["work", "focus"],
    },
    "note.updated": {
        "note_id": "note-123",
        "user_id": "user-123",
        "title": "Deep Work Revised",
        "content_md": "Updated note body",
        "tags": ["work"],
    },
    "note.link.created": {
        "source_note_id": "note-123",
        "target_note_id": "note-456",
        "user_id": "user-123",
    },
    "habit.created": {
        "habit_id": "habit-123",
        "user_id": "user-123",
    },
    "habit.completed": {
        "habit_id": "habit-123",
        "user_id": "user-123",
        "streak": 7,
    },
    "habit.streak.updated": {
        "habit_id": "habit-123",
        "user_id": "user-123",
        "streak": 7,
    },
    "habit.reminder.due": {
        "habit_id": "habit-123",
        "user_id": "user-123",
        "habit_name": "Morning Meditation",
    },
    "learning.session.logged": {
        "session_id": "session-123",
        "user_id": "user-123",
        "topic": "Kafka Basics",
        "duration": 45,
        "notes": "Studied consumer groups",
    },
    "learning.session.started": {
        "session_id": "session-123",
        "user_id": "user-123",
        "topic": "Kafka Basics",
        "start_time": "2026-03-20T10:00:00Z",
    },
    "learning.session.completed": {
        "session_id": "session-123",
        "user_id": "user-123",
        "topic": "Kafka Basics",
        "duration": 45,
        "start_time": "2026-03-20T10:00:00Z",
        "end_time": "2026-03-20T10:45:00Z",
    },
    "learning.topic.created": {
        "topic_id": "topic-123",
        "user_id": "user-123",
        "name": "Kafka Basics",
    },
    "meal.logged": {
        "log_id": "meal-123",
        "user_id": "user-123",
        "calories": 640,
        "description": "Lunch bowl",
    },
    "workout.logged": {
        "log_id": "workout-123",
        "user_id": "user-123",
        "duration": 30,
        "calories": 220,
        "description": "Strength session",
    },
    "user.registered": {
        "user_id": "user-123",
        "email": "user@example.com",
    },
    "user.login": {
        "user_id": "user-123",
    },
    "ai.interaction.completed": {
        "interaction_id": "interaction-123",
        "user_id": "user-123",
        "type": "summary",
    },
    "note.deleted": {
        "note_id": "note-123",
        "user_id": "user-123",
    },
    "health.stats.updated": {
        "user_id": "user-123",
        "date": "2026-03-22",
        "calories_consumed": 2000,
        "calories_burned": 500,
        "net_calories": 1500,
    },
}

DLQ_SAMPLE = {
    "original_topic": "note.created",
    "original_event_id": "event-123",
    "original_event_type": "note.created",
    "original_payload": EVENT_SAMPLES["note.created"],
    "error": "boom",
}


def _registered_event_types() -> set[str]:
    event_types = set()
    for path in SCHEMA_DIR.glob("*.json"):
        if path.name == "__dlq__.json":
            continue
        event_types.add(json.loads(path.read_text(encoding="utf-8"))["event_type"])
    return event_types


def test_every_registered_schema_has_a_contract_sample():
    assert _registered_event_types() == set(EVENT_SAMPLES)


@pytest.mark.parametrize(
    ("event_type", "payload"),
    sorted(EVENT_SAMPLES.items()),
)
def test_contract_samples_validate_against_registered_schemas(event_type, payload):
    event = BaseEvent(
        event_type=event_type,
        source_service="contract-test",
        payload=payload,
    )

    schema = validate_event(event)

    assert schema.event_type == event_type
    assert schema.schema_version == event.schema_version


def test_dlq_contract_sample_validates_against_registered_schema():
    event = BaseEvent(
        event_type="note.created.dlq",
        source_service="contract-test",
        payload=DLQ_SAMPLE,
    )

    schema = validate_event(event)

    assert schema.event_type == "*.dlq"
