"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

import json
from typing import Any, Optional

from aiokafka import AIOKafkaProducer
from backend.shared.config.settings import get_settings
from backend.shared.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

_producer: Optional[AIOKafkaProducer] = None


async def get_producer() -> AIOKafkaProducer:
    """Return a singleton Kafka producer, creating it on first call."""
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_broker,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            retry_backoff_ms=500,
            request_timeout_ms=30000,
        )
        await _producer.start()
        logger.info("Kafka producer started", extra={"service": settings.service_name})
    return _producer


async def send_event(
    topic: str,
    value: dict[str, Any],
    key: Optional[str] = None,
) -> None:
    """
    Publish an event to the given Kafka topic with automatic retry.

    Args:
        topic: Kafka topic name.
        value: Dictionary payload to publish.
        key: Optional partition key.
    """
    producer = await get_producer()
    try:
        await producer.send_and_wait(topic, value=value, key=key)
        logger.info(
            f"Event published to {topic}",
            extra={"service": settings.service_name},
        )
    except Exception as exc:
        logger.error(
            f"Failed to publish event to {topic}: {exc}",
            extra={"service": settings.service_name},
        )
        raise


async def close_producer() -> None:
    """Gracefully close the Kafka producer."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")
