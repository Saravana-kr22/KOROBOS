"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Messaging Library — async Kafka consumer utilities and base class.
"""

import json
import asyncio
from abc import ABC, abstractmethod
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
    Primitive async consumer for simple topics.
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
    logger.info(f"Kafka consumer started for '{topic}' (group={group_id})")

    try:
        async for msg in consumer:
            try:
                await handler(msg.value)
            except Exception as exc:
                logger.error(f"Error processing message from {topic}: {exc}")
    finally:
        await consumer.stop()


class BaseEventConsumer(ABC):
    """
    Base class for service-level event consumers.
    Handles the Kafka event loop with error handling and logging.
    """

    def __init__(self, topics: list[str], group_id: str):
        self.topics = topics
        self.group_id = group_id
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._running = False

    async def start(self):
        """Start the consumer background task."""
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=settings.kafka_broker,
            group_id=self.group_id,
            auto_offset_reset="earliest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            enable_auto_commit=True,
        )
        await self.consumer.start()
        self._running = True
        logger.info(
            "Consumer group '%s' started for topics: %s",
            self.group_id,
            self.topics,
        )

        asyncio.create_task(self._consume_loop())

    async def _consume_loop(self):
        """Internal message processing loop."""
        try:
            async for msg in self.consumer:
                if not self._running:
                    break
                try:
                    await self.handle_event(msg.topic, msg.value)
                except Exception as exc:
                    logger.error(
                        "Consumer error in group '%s' on topic '%s': %s",
                        self.group_id,
                        msg.topic,
                        exc,
                    )
        finally:
            await self.stop()

    @abstractmethod
    async def handle_event(self, topic: str, payload: dict[str, Any]):
        """Override this method to process events."""
        pass

    async def stop(self):
        """Gracefully stop the consumer."""
        self._running = False
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None
            logger.info(f"Consumer group '{self.group_id}' stopped")
