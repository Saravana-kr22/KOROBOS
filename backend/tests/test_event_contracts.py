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
    "learning.session.logged": {
        "session_id": "session-123",
        "user_id": "user-123",
        "topic": "Kafka Basics",
        "duration": 45,
        "notes": "Studied consumer groups",
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
