"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Messaging Library — async Kafka consumer utilities and base class.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import OffsetAndMetadata, TopicPartition
from backend.shared.config.settings import get_settings
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.kafka_config import build_kafka_client_options
from backend.shared.messaging.producer import publish_event
from backend.shared.messaging.schemas import BaseEvent

logger = get_logger(__name__)
settings = get_settings()


async def create_consumer(
    topic: str,
    group_id: str,
    handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    auto_offset_reset: str = "earliest",
) -> None:
    """Primitive async consumer for simple topics."""
    consumer = AIOKafkaConsumer(
        topic,
        **build_kafka_client_options(settings),
        group_id=group_id,
        auto_offset_reset=auto_offset_reset,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        enable_auto_commit=False,
    )

    await consumer.start()
    logger.info(f"Kafka consumer started for '{topic}' (group={group_id})")

    try:
        async for msg in consumer:
            try:
                await handler(msg.value)
                await consumer.commit(
                    {
                        TopicPartition(msg.topic, msg.partition): OffsetAndMetadata(
                            msg.offset + 1,
                            "",
                        )
                    }
                )
            except Exception as exc:
                logger.error(f"Error processing message from {topic}: {exc}")
                raise
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
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the consumer background task."""
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            **build_kafka_client_options(settings),
            group_id=self.group_id,
            auto_offset_reset="earliest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            enable_auto_commit=False,
        )
        await self.consumer.start()
        self._running = True
        logger.info(
            "Consumer group '%s' started for topics: %s",
            self.group_id,
            self.topics,
        )

        self._task = asyncio.create_task(self._consume_loop())

    async def _consume_loop(self):
        """
        Internal message processing loop with retry and DLQ handling.

        Retry policy (from Sprint 4 spec):
          - Attempt 1 → immediate
          - Attempt 2 → after 5 seconds
          - Attempt 3 → after 30 seconds

        After all attempts fail the message is forwarded to a '*.dlq' topic.
        """
        try:
            async for msg in self.consumer:
                if not self._running:
                    break
                await self._handle_record(msg)
        finally:
            await self.stop()

    async def _handle_record(self, msg) -> None:
        """Process a single Kafka record and commit its offset on success."""
        processed = await self._process_message(msg.topic, msg.value)
        if not processed:
            raise RuntimeError(
                "Failed to process Kafka record "
                f"{msg.topic}@{msg.partition}:{msg.offset}"
            )

        await self.consumer.commit(
            {
                TopicPartition(msg.topic, msg.partition): OffsetAndMetadata(
                    msg.offset + 1,
                    "",
                )
            }
        )

    async def _process_message(self, topic: str, payload: dict[str, Any]) -> bool:
        """Apply retry strategy before delegating to handle_event."""
        delays = [0, 5, 30]
        last_exc: Optional[Exception] = None

        for delay in delays:
            if not self._running:
                return False
            if delay:
                await asyncio.sleep(delay)
            try:
                await self.handle_event(topic, payload)
                return True
            except Exception as exc:
                last_exc = exc
                logger.error(
                    "Consumer error in group '%s' on topic '%s' (will retry): %s",
                    self.group_id,
                    topic,
                    exc,
                )

        if last_exc is not None:
            return await self._send_to_dlq(topic, payload, last_exc)
        return False

    async def _send_to_dlq(
        self,
        topic: str,
        payload: dict[str, Any],
        exc: Exception,
    ) -> bool:
        """Publish failed messages to a Dead Letter Queue topic."""
        dlq_topic = f"{topic}.dlq"
        try:
            event = BaseEvent(
                event_type=dlq_topic,
                source_service=settings.service_name,
                payload={
                    "original_topic": topic,
                    "original_event_id": payload.get("event_id"),
                    "original_event_type": payload.get("event_type", topic),
                    "original_payload": payload.get("payload", payload),
                    "error": str(exc),
                },
            )
            await publish_event(event)
            logger.error(
                "Message moved to DLQ topic '%s' from '%s'",
                dlq_topic,
                topic,
            )
            return True
        except Exception as dlq_exc:
            logger.error(
                "Failed to publish message to DLQ topic '%s' from '%s': %s",
                dlq_topic,
                topic,
                dlq_exc,
            )
            return False

    @abstractmethod
    async def handle_event(self, topic: str, payload: dict[str, Any]):
        """Override this method to process events."""
        pass

    async def stop(self):
        """Gracefully stop the consumer."""
        self._running = False
        if self._task and self._task is not asyncio.current_task():
            self._task.cancel()
            self._task = None
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None
            logger.info(f"Consumer group '{self.group_id}' stopped")
