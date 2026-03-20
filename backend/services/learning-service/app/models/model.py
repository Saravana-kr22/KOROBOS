"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM models for the Learning Service.

.. deprecated::
    Import from ``session_model`` / ``topic_model`` directly
    (Sprint_9.md file-naming convention).  This module re-exports
    all symbols for backward compatibility.
"""

# Re-export from canonical locations (Sprint_9.md naming)
from .session_model import LearningSession, SessionNote  # noqa: F401
from .topic_model import Topic  # noqa: F401
