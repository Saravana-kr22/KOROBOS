"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

.. deprecated:: Re-export shim — import from ``learning_schema`` directly.
"""

# Re-export all symbols from canonical location
from app.schemas.learning_schema import (  # noqa: F401
    LearningSessionCreate,
    LearningSessionListResponse,
    LearningSessionResponse,
    LearningSessionUpdate,
    LearningStatsResponse,
    LinkNoteRequest,
    SessionNotesResponse,
    SessionPauseRequest,
    SessionResumeRequest,
    SessionStartRequest,
    SessionStopRequest,
    TopicCreate,
    TopicListResponse,
    TopicResponse,
    TopicUpdate,
)
