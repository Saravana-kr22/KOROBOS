"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from pydantic import Field

from backend.shared.config.settings import KOROBOSSettings


class AnalyticsSettings(KOROBOSSettings):
    """Service-specific settings for Analytics Service."""

    # ClickHouse configuration for OLAP analytics
    clickhouse_url: str = Field(
        default="http://localhost:8123",
        description="ClickHouse HTTP interface URL",
    )
    clickhouse_user: str = Field(
        default="default",
        description="ClickHouse username",
    )
    clickhouse_password: str = Field(
        default="clickhouse",
        description="ClickHouse password",
    )
    clickhouse_database: str = Field(
        default="korobos",
        description="ClickHouse database name",
    )

    model_config = {
        "env_prefix": "ANALYTICS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }
