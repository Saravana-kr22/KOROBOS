"""
Pure event-to-action transforms used by worker handlers.
"""

from typing import Any


def analytics_metric_for_event(
    event_type: str, payload: dict[str, Any]
) -> tuple[str, float] | None:
    if event_type == "note.created":
        return "notes.created", 1.0
    if event_type == "note.link.created":
        return "notes.links.created", 1.0
    if event_type == "habit.created":
        return "habits.created", 1.0
    if event_type == "habit.completed":
        return "habits.completed", float(payload.get("streak", 1))
    if event_type == "learning.session.logged":
        return "learning.minutes", float(payload.get("duration", 0))
    if event_type == "meal.logged":
        return "calories.intake", float(payload.get("calories", 0))
    if event_type == "workout.logged":
        return "workout.minutes", float(payload.get("duration", 0))
    if event_type == "user.registered":
        return "users.registered", 1.0
    if event_type == "user.login":
        return "auth.logins", 1.0
    if event_type == "ai.interaction.completed":
        return "ai.interactions.completed", 1.0
    return None


def notification_content_for_event(
    event_type: str, payload: dict[str, Any]
) -> tuple[str, str] | None:
    if event_type == "habit.completed":
        streak = payload.get("streak")
        title = "Habit completed 🎯"
        if streak:
            body = f"Great job! Your current streak is {streak} days."
        else:
            body = "Great job completing your habit today!"
        return title, body
    return None


def search_document_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": payload["note_id"],
        "note_id": payload["note_id"],
        "user_id": payload["user_id"],
        "title": payload.get("title", ""),
        "content_md": payload.get("content_md", ""),
        "tags": payload.get("tags", []),
    }


def ai_prompt_for_event(
    event_type: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    if event_type == "note.created":
        title = payload.get("title", "Untitled note")
        content_md = payload.get("content_md", "")
        return {
            "interaction_type": "summary",
            "prompt": (
                "Create a concise summary and action items for the note "
                f"'{title}'.\n\n{content_md}"
            ),
            "metadata_json": {
                "source_event": event_type,
                "note_id": payload.get("note_id"),
            },
        }

    if event_type == "note.updated":
        title = payload.get("title", payload.get("note_id", "updated note"))
        content_md = payload.get("content_md", "")
        return {
            "interaction_type": "summary",
            "prompt": (
                "Refresh the summary and key takeaways for the note "
                f"'{title}'.\n\n{content_md}"
            ),
            "metadata_json": {
                "source_event": event_type,
                "note_id": payload.get("note_id"),
            },
        }

    if event_type == "learning.session.logged":
        topic = payload.get("topic", "learning session")
        duration = payload.get("duration", 0)
        notes = payload.get("notes", "")
        return {
            "interaction_type": "recommendation",
            "prompt": (
                f"Suggest the next best learning steps for '{topic}' after "
                f"{duration} minutes of study.\n\n{notes}"
            ),
            "metadata_json": {
                "source_event": event_type,
                "session_id": payload.get("session_id"),
            },
        }

    return None
