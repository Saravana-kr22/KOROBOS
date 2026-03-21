"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

.. deprecated:: Re-export shim — import from ``session_repository`` directly.
"""

# Re-export canonical class
from app.repositories.session_repository import LearningRepository  # noqa: F401
