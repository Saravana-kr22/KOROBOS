"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service configuration.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class DashboardSettings(BaseSettings):
    """
    Dashboard Service configuration.

    Extends shared KOROBOSSettings with service-specific URLs for internal
    service discovery (habits, health, learning) and other settings.
    """

    # ── Service URLs ──
    # Internal URLs for calling source services via httpx
    analytics_service_url: str = Field(
        default="http://analytics-service:8000",
        description="Analytics Service base URL",
    )
    habit_service_url: str = Field(
        default="http://habit-service:8000",
        description="Habit Service base URL",
    )
    health_service_url: str = Field(
        default="http://health-service:8000",
        description="Health Service base URL",
    )
    learning_service_url: str = Field(
        default="http://learning-service:8000",
        description="Learning Service base URL",
    )
    notes_service_url: str = Field(
        default="http://notes-service:8000",
        description="Notes Service base URL",
    )
    database_service_url: str = Field(
        default="http://database-service:8000",
        description="Database Service base URL",
    )

    # ── Database ──
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost/korobos_dev",
        description="Database connection URL",
    )

    # ── Redis ──
    redis_url: str = Field(
        default="redis://localhost:6379/1",
        description="Redis URL for caching",
    )

    # ── Kafka ──
    kafka_broker: str = Field(
        default="localhost:9092",
        description="Kafka broker address",
    )

    # ── JWT ──
    jwt_secret: str = Field(
        default="change-me-in-production",
        description="JWT signing secret",
    )

    # ── Environment ──
    environment: str = Field(
        default="development",
        description="Deployment environment",
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> DashboardSettings:
    """Return a cached singleton of dashboard settings."""
    return DashboardSettings()
