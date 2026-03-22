"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from functools import lru_cache

from pydantic import Field

from backend.shared.config.settings import KOROBOSSettings


class AiSettings(KOROBOSSettings):
    """Service-specific settings for Ai Service."""

    # ── Inter-service URLs ──
    analytics_service_url: str = Field(
        default="http://localhost:8005",
        description="Analytics service base URL",
    )
    graph_service_url: str = Field(
        default="http://localhost:8011",
        description="Graph service base URL",
    )

    model_config = {
        "env_prefix": "AI_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> AiSettings:
    """Return a cached singleton of the AI service settings."""
    return AiSettings()
