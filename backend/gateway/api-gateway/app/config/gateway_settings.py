"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Gateway-specific configuration extending the shared KOROBOS settings.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    """
    Configuration for the API Gateway.

    Service URLs are read from environment variables so that Docker Compose
    or Kubernetes can inject the correct addresses.
    """

    # ── Service URLs ──
    services_auth: str = Field(
        default="http://localhost:8000",
        description="Auth service base URL",
    )
    services_notes: str = Field(
        default="http://localhost:8001",
        description="Notes service base URL",
    )
    services_habits: str = Field(
        default="http://localhost:8002",
        description="Habit service base URL",
    )
    services_learning: str = Field(
        default="http://localhost:8003",
        description="Learning service base URL",
    )
    services_health: str = Field(
        default="http://localhost:8004",
        description="Health service base URL",
    )
    services_analytics: str = Field(
        default="http://localhost:8005",
        description="Analytics service base URL",
    )
    services_notifications: str = Field(
        default="http://localhost:8006",
        description="Notification service base URL",
    )
    services_ai: str = Field(
        default="http://localhost:8007",
        description="AI service base URL",
    )

    # ── Security ──
    jwt_secret: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT verification",
    )

    # ── Rate Limiting ──
    rate_limit_per_user: int = Field(
        default=100,
        description="Max requests per minute per authenticated user",
    )
    rate_limit_per_ip: int = Field(
        default=1000,
        description="Max requests per minute per IP address",
    )

    # ── Redis ──
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for rate-limiting counters",
    )

    # ── CORS ──
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins. Override in production.",
    )

    # ── Paths that skip authentication ──
    public_paths: list[str] = Field(
        default=[
            "/health",
            "/metrics",
            "/metrics/prometheus",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/auth/login",
            "/api/v1/auth/signup",
            "/api/v1/auth/register",
        ],
        description="Paths that do not require JWT authentication",
    )

    model_config = {
        "env_prefix": "",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_gateway_settings() -> GatewaySettings:
    """Return a cached singleton of gateway settings."""
    return GatewaySettings()
