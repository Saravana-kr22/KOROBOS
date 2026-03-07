"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

import json
from typing import Any, Callable, Coroutine, Optional

from aiokafka import AIOKafkaConsumer

from backend.shared.config.settings import get_settings
from backend.shared.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def create_consumer(
    topic: str,
    group_id: str,
    handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    auto_offset_reset: str = "earliest",
) -> None:
    """
    Start a Kafka consumer that processes messages with the given handler.

    Args:
        topic: Kafka topic to consume from.
        group_id: Consumer group ID.
        handler: Async callable invoked for each message value.
        auto_offset_reset: Where to start reading if no offset is committed.
    """
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.kafka_broker,
        group_id=group_id,
        auto_offset_reset=auto_offset_reset,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        enable_auto_commit=True,
    )

    await consumer.start()
    logger.info(
        f"Kafka consumer started for topic '{topic}' (group={group_id})",
        extra={"service": settings.service_name},
    )

    try:
        async for msg in consumer:
            try:
                await handler(msg.value)
            except Exception as exc:
                logger.error(
                    f"Error processing message from {topic}: {exc}",
                    extra={"service": settings.service_name},
                )
    finally:
        await consumer.stop()
        logger.info(f"Kafka consumer stopped for topic '{topic}'")
