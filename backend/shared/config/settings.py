"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class CortexOSSettings(BaseSettings):
    """
    Centralized, typed configuration for CortexOS microservices.

    Features:
      - environment variable parsing (automatic via pydantic-settings)
      - typed configuration with defaults
      - secret loading from environment
      - runtime validation via pydantic validators
    """

    # ── Core ──
    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")

    # ── Database ──
    database_url: str = Field(
        default="postgresql+asyncpg://cortexos:password@localhost:5432/cortexos",
        description="Async PostgreSQL connection string",
    )

    # ── Redis ──
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # ── Kafka ──
    kafka_broker: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap server(s)",
    )
    kafka_security_protocol: str = Field(
        default="PLAINTEXT",
        description="Kafka security protocol (PLAINTEXT, SSL, SASL_SSL, etc.)",
    )
    kafka_sasl_mechanism: str = Field(
        default="PLAIN",
        description="Kafka SASL mechanism when SASL is enabled",
    )
    kafka_sasl_username: str = Field(
        default="",
        description="Kafka SASL username",
    )
    kafka_sasl_password: str = Field(
        default="",
        description="Kafka SASL password",
    )
    kafka_ssl_ca_file: str = Field(
        default="",
        description="Optional CA bundle used for Kafka TLS verification",
    )
    kafka_ssl_cert_file: str = Field(
        default="",
        description="Optional client certificate for Kafka TLS auth",
    )
    kafka_ssl_key_file: str = Field(
        default="",
        description="Optional client private key for Kafka TLS auth",
    )
    kafka_ssl_check_hostname: bool = Field(
        default=True,
        description="Whether to verify Kafka broker hostnames for TLS",
    )

    # ── Search ──
    search_url: str = Field(
        default="http://localhost:7700",
        description="Meilisearch URL",
    )
    search_api_key: str = Field(
        default="",
        description="Optional API key for the search backend",
    )

    # ── Object Storage ──
    object_storage_url: str = Field(
        default="http://localhost:9000",
        description="S3-compatible object storage URL",
    )

    # ── Secrets ──
    jwt_secret: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT signing",
    )

    # ── Service ──
    service_name: str = Field(default="cortexos", description="Name of this service")
    service_port: int = Field(default=8000, description="Port this service listens on")
    log_level: str = Field(default="INFO", description="Logging level")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got '{v}'")
        return v

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, v):
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in {"release", "prod", "production", "off"}:
                return False
            if normalized in {"debug", "dev", "development", "on"}:
                return True
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return v_upper

    @field_validator("kafka_security_protocol")
    @classmethod
    def validate_kafka_security_protocol(cls, v: str) -> str:
        allowed = {"PLAINTEXT", "SSL", "SASL_PLAINTEXT", "SASL_SSL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(
                "kafka_security_protocol must be one of "
                f"{allowed}, got '{v}'"
            )
        return v_upper

    @field_validator("kafka_sasl_mechanism")
    @classmethod
    def validate_kafka_sasl_mechanism(cls, v: str) -> str:
        allowed = {"PLAIN", "SCRAM-SHA-256", "SCRAM-SHA-512"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(
                f"kafka_sasl_mechanism must be one of {allowed}, got '{v}'"
            )
        return v_upper

    model_config = {
        "env_prefix": "",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> CortexOSSettings:
    """Return a cached singleton of the application settings."""
    return CortexOSSettings()
