"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Service-specific settings for the Auth Service.
"""

from backend.shared.config.settings import CortexOSSettings


class AuthSettings(CortexOSSettings):
    """Auth-specific settings."""

    model_config = {
        "env_prefix": "AUTH_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }
