"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from backend.shared.config.settings import CortexOSSettings


class NotificationSettings(CortexOSSettings):
    """Service-specific settings for Notification Service."""
    
    model_config = {
        "env_prefix": "NOTIFICATION_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }
