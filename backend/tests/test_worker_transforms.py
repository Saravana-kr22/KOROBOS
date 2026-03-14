"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Worker-level tests for topic coverage and event transforms.
"""

from backend.workers.event_transforms import (
    ai_prompt_for_event,
    analytics_metric_for_event,
    notification_content_for_event,
    search_document_from_payload,
)
from backend.workers.topics import (
    AI_TOPICS,
    ANALYTICS_TOPICS,
    NOTIFICATION_TOPICS,
    SEARCH_TOPICS,
)

PRODUCED_ACTIVITY_TOPICS = {
    "note.created",
    "note.updated",
    "note.link.created",
    "habit.created",
    "habit.completed",
    "learning.session.logged",
    "meal.logged",
    "workout.logged",
    "user.registered",
    "user.login",
    "ai.interaction.completed",
}


def test_all_produced_activity_topics_have_at_least_one_worker_subscription():
    subscribed_topics = (
        set(ANALYTICS_TOPICS)
        | set(NOTIFICATION_TOPICS)
        | set(SEARCH_TOPICS)
        | set(AI_TOPICS)
    )

    assert PRODUCED_ACTIVITY_TOPICS <= subscribed_topics


def test_analytics_transform_covers_new_activity_topics():
    assert analytics_metric_for_event("note.link.created", {"user_id": "user-1"}) == (
        "notes.links.created",
        1.0,
    )
    assert analytics_metric_for_event("habit.created", {"user_id": "user-1"}) == (
        "habits.created",
        1.0,
    )
    assert analytics_metric_for_event("user.registered", {"user_id": "user-1"}) == (
        "users.registered",
        1.0,
    )
    assert analytics_metric_for_event("user.login", {"user_id": "user-1"}) == (
        "auth.logins",
        1.0,
    )
    assert analytics_metric_for_event(
        "ai.interaction.completed",
        {"user_id": "user-1"},
    ) == ("ai.interactions.completed", 1.0)


def test_notification_transform_formats_habit_completion():
    title, body = notification_content_for_event(
        "habit.completed",
        {"streak": 9},
    )

    assert title == "Habit completed 🎯"
    assert "9 days" in body


def test_search_transform_preserves_searchable_note_fields():
    document = search_document_from_payload(
        {
            "note_id": "note-123",
            "user_id": "user-123",
            "title": "Deep Work",
            "content_md": "Focus block notes",
            "tags": ["focus", "planning"],
        }
    )

    assert document == {
        "id": "note-123",
        "note_id": "note-123",
        "user_id": "user-123",
        "title": "Deep Work",
        "content_md": "Focus block notes",
        "tags": ["focus", "planning"],
    }


def test_ai_transform_builds_prompts_for_note_updates_and_learning_events():
    note_prompt = ai_prompt_for_event(
        "note.updated",
        {
            "note_id": "note-123",
            "title": "Weekly Review",
            "content_md": "Inbox zero and planning notes",
        },
    )
    learning_prompt = ai_prompt_for_event(
        "learning.session.logged",
        {
            "session_id": "session-123",
            "topic": "Kafka",
            "duration": 60,
            "notes": "Studied retries and DLQs",
        },
    )

    assert note_prompt is not None
    assert "Weekly Review" in note_prompt["prompt"]
    assert note_prompt["metadata_json"]["note_id"] == "note-123"
    assert learning_prompt is not None
    assert "60 minutes" in learning_prompt["prompt"]
    assert learning_prompt["metadata_json"]["session_id"] == "session-123"
