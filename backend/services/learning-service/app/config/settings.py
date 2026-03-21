"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from functools import lru_cache

from backend.shared.config.settings import KOROBOSSettings


class LearningSettings(KOROBOSSettings):
    """Service-specific settings for Learning Service."""

    model_config = {
        "env_prefix": "LEARNING_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> LearningSettings:
    return LearningSettings()
