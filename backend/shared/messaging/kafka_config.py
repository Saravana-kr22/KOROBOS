"""
Kafka client configuration helpers shared by producers and consumers.
"""

import ssl
from typing import Any

from backend.shared.config.settings import CortexOSSettings


def build_kafka_client_options(settings: CortexOSSettings) -> dict[str, Any]:
    """
    Build aiokafka connection options from settings.

    Supports plaintext, TLS, and SASL-over-TLS configurations so services and
    workers can share one transport configuration path.
    """

    options: dict[str, Any] = {
        "bootstrap_servers": settings.kafka_broker,
    }
    protocol = settings.kafka_security_protocol

    if protocol != "PLAINTEXT":
        options["security_protocol"] = protocol

    if "SSL" in protocol:
        ssl_context = _build_ssl_context(settings)
        options["ssl_context"] = ssl_context

    if protocol.startswith("SASL_"):
        if not settings.kafka_sasl_username or not settings.kafka_sasl_password:
            raise ValueError(
                "Kafka SASL credentials are required when SASL is enabled"
            )
        options["sasl_mechanism"] = settings.kafka_sasl_mechanism
        options["sasl_plain_username"] = settings.kafka_sasl_username
        options["sasl_plain_password"] = settings.kafka_sasl_password

    return options


def _build_ssl_context(settings: CortexOSSettings) -> ssl.SSLContext:
    if settings.kafka_ssl_ca_file:
        ssl_context = ssl.create_default_context(cafile=settings.kafka_ssl_ca_file)
    else:
        ssl_context = ssl.create_default_context()

    ssl_context.check_hostname = settings.kafka_ssl_check_hostname

    if settings.kafka_ssl_cert_file and settings.kafka_ssl_key_file:
        ssl_context.load_cert_chain(
            settings.kafka_ssl_cert_file,
            settings.kafka_ssl_key_file,
        )

    return ssl_context
