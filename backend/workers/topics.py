"""
Canonical Kafka topic subscriptions for CortexOS background workers.
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
