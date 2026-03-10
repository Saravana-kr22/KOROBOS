"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Integration tests that exercise the messaging stack with Kafka.
"""

import asyncio
from uuid import uuid4

import pytest
from backend.shared.messaging.consumer import BaseEventConsumer
from backend.shared.messaging.producer import close_producer, publish_event
from backend.shared.messaging.schemas import BaseEvent


class _IntegrationConsumer(BaseEventConsumer):
    def __init__(self, group_id: str):
        super().__init__(topics=["note.created"], group_id=group_id)
        self.received = asyncio.Event()
        self.payload = None

    async def handle_event(self, topic: str, payload: dict):
        self.payload = {"topic": topic, "payload": payload}
        self.received.set()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_publish_and_consume_with_real_kafka(monkeypatch):
    import backend.shared.messaging.consumer as consumer_module
    import backend.shared.messaging.producer as producer_module

    pytest.importorskip(
        "testcontainers.kafka",
        reason="Backend dev dependencies are missing testcontainers[kafka].",
    )
    import docker.errors
    from testcontainers.kafka import KafkaContainer

    try:
        container = KafkaContainer()
    except (docker.errors.DockerException, PermissionError) as exc:
        pytest.skip(f"Docker unavailable for testcontainers: {exc}")

    try:
        try:
            container.start()
        except (docker.errors.DockerException, PermissionError, OSError) as exc:
            pytest.skip(f"Docker unavailable for testcontainers: {exc}")
        except Exception as exc:
            pytest.skip(f"Kafka test container unavailable: {exc}")

        bootstrap_server = container.get_bootstrap_server()
        monkeypatch.setattr(
            producer_module.settings,
            "kafka_broker",
            bootstrap_server,
            raising=False,
        )
        monkeypatch.setattr(
            consumer_module.settings,
            "kafka_broker",
            bootstrap_server,
            raising=False,
        )

        await close_producer()

        event = BaseEvent(
            event_type="note.created",
            source_service="integration-test",
            payload={
                "note_id": "note-123",
                "user_id": "user-123",
                "title": "Integration Test",
                "content_md": "Kafka round-trip",
                "tags": ["integration"],
            },
        )
        await publish_event(event, key="user-123")

        consumer = _IntegrationConsumer(group_id=f"it-{uuid4()}")
        await consumer.start()
        try:
            await asyncio.wait_for(consumer.received.wait(), timeout=30)
            assert consumer.payload is not None
            assert consumer.payload["topic"] == "note.created"
            assert consumer.payload["payload"]["payload"]["title"] == "Integration Test"
        finally:
            await consumer.stop()
            await close_producer()
    finally:
        try:
            container.stop()
        except Exception:
            pass
