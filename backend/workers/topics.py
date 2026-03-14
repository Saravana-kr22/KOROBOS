"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Canonical Kafka topic subscriptions for KOROBOS background workers.
"""

ANALYTICS_TOPICS = (
    "note.created",
    "note.link.created",
    "habit.created",
    "habit.completed",
    "learning.session.logged",
    "meal.logged",
    "workout.logged",
    "user.registered",
    "user.login",
    "ai.interaction.completed",
)

NOTIFICATION_TOPICS = ("habit.completed",)

SEARCH_TOPICS = (
    "note.created",
    "note.updated",
)

AI_TOPICS = (
    "note.created",
    "note.updated",
    "learning.session.logged",
)
