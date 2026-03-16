"""
KOROBOS — Database Service Configuration

Settings for the database service.
"""

from functools import lru_cache

from backend.shared.config.settings import KOROBOSSettings


class DatabaseSettings(KOROBOSSettings):
    """Database service configuration."""

    model_config = {
        "env_prefix": "DATABASE_SERVICE_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> DatabaseSettings:
    """Get cached settings instance."""
    return DatabaseSettings()
