"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

import asyncio
import json
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

from backend.shared.config.settings import get_settings
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.kafka_config import build_kafka_client_options
from backend.shared.messaging.schema_registry import (
    EventValidationError,
    infer_partition_key,
    validate_event,
)
from backend.shared.messaging.schemas import BaseEvent

logger = get_logger(__name__)
settings = get_settings()

_producer: Optional[AIOKafkaProducer] = None


class EventPublishError(RuntimeError):
    """Raised when an event cannot be validated or published."""


async def get_producer() -> AIOKafkaProducer:
    """Return a singleton Kafka producer, creating it on first call."""
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            **build_kafka_client_options(settings),
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            enable_idempotence=True,
            acks="all",
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
    retries: int = 3,
) -> None:
    """
    Low-level event publisher used by higher-level helpers.

    Args:
        topic: Kafka topic name (typically event_type, e.g. 'note.created').
        value: Dictionary payload to publish (already validated).
        key: Optional partition key (e.g. user_id / note_id).
    """
    producer = await get_producer()
    delays = [0, 5, 30]
    last_exc: Optional[Exception] = None

    for attempt, delay in enumerate(delays[:retries], start=1):
        if delay:
            await asyncio.sleep(delay)
        try:
            await producer.send_and_wait(topic, value=value, key=key)
            logger.info(
                "Event published to topic '%s'",
                topic,
                extra={"service": settings.service_name},
            )
            return
        except Exception as exc:
            last_exc = exc
            logger.error(
                "Failed to publish event to topic '%s' on attempt %s/%s: %s",
                topic,
                attempt,
                min(retries, len(delays)),
                exc,
                extra={"service": settings.service_name},
            )

    raise EventPublishError(f"Failed to publish event to topic '{topic}'") from last_exc


async def publish_event(event: BaseEvent, key: Optional[str] = None) -> None:
    """
    High-level helper that publishes a typed BaseEvent instance.

    The Kafka topic defaults to the event_type (e.g. 'note.created'), which
    matches the topic design defined in the Sprint 4 event bus documentation.
    """
    try:
        schema = validate_event(event)
    except EventValidationError as exc:
        raise EventPublishError(
            f"Event validation failed for '{event.event_type}'"
        ) from exc

    resolved_key = key or infer_partition_key(event, schema)
    payload = event.model_dump(by_alias=True, mode="json")
    await send_event(topic=event.event_type, value=payload, key=resolved_key)


async def close_producer() -> None:
    """Gracefully close the Kafka producer."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")
