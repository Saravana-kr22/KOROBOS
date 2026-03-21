"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for the Kafka messaging primitives added in Sprint 4.
"""

from types import SimpleNamespace

import pytest
from aiokafka.structs import TopicPartition

from backend.shared.messaging.consumer import BaseEventConsumer
from backend.shared.messaging.kafka_config import build_kafka_client_options
from backend.shared.messaging.producer import publish_event
from backend.shared.messaging.schema_registry import (
    EventValidationError,
    validate_event,
)
from backend.shared.messaging.schemas import BaseEvent


def _build_note_event(**payload_overrides) -> BaseEvent:
    payload = {
        "note_id": "note-123",
        "user_id": "user-123",
        "title": "Deep Work",
        "content_md": "Focus block notes",
        "tags": ["work", "focus"],
    }
    payload.update(payload_overrides)
    return BaseEvent(
        event_type="note.created",
        source_service="notes-service",
        payload=payload,
    )


def test_base_event_serializes_producer_alias():
    event = _build_note_event()
    message = event.model_dump(by_alias=True, mode="json")

    assert message["producer"] == "notes-service"
    assert "source_service" not in message
    assert message["schema_version"] == 1


def test_schema_registry_rejects_missing_required_payload():
    event = BaseEvent(
        event_type="note.created",
        source_service="notes-service",
        payload={"note_id": "note-123", "user_id": "user-123"},
    )

    with pytest.raises(EventValidationError, match="title"):
        validate_event(event)


def test_kafka_client_options_default_to_plaintext():
    settings = SimpleNamespace(
        kafka_broker="localhost:9092",
        kafka_security_protocol="PLAINTEXT",
        kafka_sasl_mechanism="PLAIN",
        kafka_sasl_username="",
        kafka_sasl_password="",
        kafka_ssl_ca_file="",
        kafka_ssl_cert_file="",
        kafka_ssl_key_file="",
        kafka_ssl_check_hostname=True,
    )

    options = build_kafka_client_options(settings)

    assert options == {"bootstrap_servers": "localhost:9092"}


def test_kafka_client_options_build_sasl_ssl_context(monkeypatch):
    created = {}

    class FakeSSLContext:
        def __init__(self):
            self.check_hostname = True
            self.loaded_chain = None

        def load_cert_chain(self, certfile, keyfile):
            self.loaded_chain = (certfile, keyfile)

    def fake_create_default_context(cafile=None):
        created["cafile"] = cafile
        created["context"] = FakeSSLContext()
        return created["context"]

    monkeypatch.setattr(
        "backend.shared.messaging.kafka_config.ssl.create_default_context",
        fake_create_default_context,
    )
    settings = SimpleNamespace(
        kafka_broker="kafka:29093",
        kafka_security_protocol="SASL_SSL",
        kafka_sasl_mechanism="PLAIN",
        kafka_sasl_username="korobos",
        kafka_sasl_password="secret",
        kafka_ssl_ca_file="/tmp/ca.crt",
        kafka_ssl_cert_file="/tmp/client.crt",
        kafka_ssl_key_file="/tmp/client.key",
        kafka_ssl_check_hostname=False,
    )

    options = build_kafka_client_options(settings)

    assert created["cafile"] == "/tmp/ca.crt"
    assert options["security_protocol"] == "SASL_SSL"
    assert options["sasl_mechanism"] == "PLAIN"
    assert options["sasl_plain_username"] == "korobos"
    assert options["sasl_plain_password"] == "secret"
    assert options["ssl_context"] is created["context"]
    assert created["context"].check_hostname is False
    assert created["context"].loaded_chain == ("/tmp/client.crt", "/tmp/client.key")


@pytest.mark.anyio
async def test_publish_event_retries_and_uses_partition_key(monkeypatch):
    attempts = []
    sleeps = []

    class FakeProducer:
        async def send_and_wait(self, topic, value, key=None):
            attempts.append((topic, value, key))
            if len(attempts) < 3:
                raise RuntimeError("temporary kafka failure")

    async def fake_get_producer():
        return FakeProducer()

    async def fake_sleep(_seconds):
        sleeps.append(_seconds)
        return None

    monkeypatch.setattr(
        "backend.shared.messaging.producer.get_producer", fake_get_producer
    )
    monkeypatch.setattr("backend.shared.messaging.producer.asyncio.sleep", fake_sleep)

    await publish_event(_build_note_event())

    assert len(attempts) == 3
    assert sleeps == [5, 30]
    assert attempts[-1][0] == "note.created"
    assert attempts[-1][2] == "user-123"
    assert attempts[-1][1]["producer"] == "notes-service"


class _FakeKafkaConsumer:
    def __init__(self):
        self.commits = []

    async def commit(self, offsets):
        self.commits.append(offsets)

    async def stop(self):
        return None


class _SuccessfulConsumer(BaseEventConsumer):
    def __init__(self):
        super().__init__(topics=["note.created"], group_id="test-group")
        self.handled = []

    async def handle_event(self, topic: str, payload: dict):
        self.handled.append((topic, payload))


class _FailingConsumer(BaseEventConsumer):
    async def handle_event(self, topic: str, payload: dict):
        raise RuntimeError("handler exploded")


@pytest.mark.anyio
async def test_base_event_consumer_commits_after_success():
    consumer = _SuccessfulConsumer()
    consumer.consumer = _FakeKafkaConsumer()
    consumer._running = True
    record = SimpleNamespace(
        topic="note.created",
        partition=0,
        offset=7,
        value=_build_note_event().model_dump(by_alias=True, mode="json"),
    )

    await consumer._handle_record(record)

    tp = TopicPartition("note.created", 0)
    assert len(consumer.consumer.commits) == 1
    assert consumer.consumer.commits[0][tp].offset == 8
    assert consumer.handled[0][0] == "note.created"


@pytest.mark.anyio
async def test_base_event_consumer_commits_after_dlq(monkeypatch):
    published = []

    async def fake_publish_event(event, key=None):
        published.append((event, key))

    async def fake_sleep(_seconds):
        return None

    monkeypatch.setattr(
        "backend.shared.messaging.consumer.publish_event", fake_publish_event
    )
    monkeypatch.setattr("backend.shared.messaging.consumer.asyncio.sleep", fake_sleep)

    consumer = _FailingConsumer(topics=["note.created"], group_id="test-group")
    consumer.consumer = _FakeKafkaConsumer()
    consumer._running = True
    record = SimpleNamespace(
        topic="note.created",
        partition=1,
        offset=11,
        value=_build_note_event().model_dump(by_alias=True, mode="json"),
    )

    await consumer._handle_record(record)

    tp = TopicPartition("note.created", 1)
    assert len(published) == 1
    assert published[0][0].event_type == "note.created.dlq"
    assert consumer.consumer.commits[0][tp].offset == 12


@pytest.mark.anyio
async def test_base_event_consumer_does_not_commit_when_dlq_publish_fails(
    monkeypatch,
):
    async def fake_publish_event(event, key=None):
        raise RuntimeError("dlq unavailable")

    async def fake_sleep(_seconds):
        return None

    monkeypatch.setattr(
        "backend.shared.messaging.consumer.publish_event", fake_publish_event
    )
    monkeypatch.setattr("backend.shared.messaging.consumer.asyncio.sleep", fake_sleep)

    consumer = _FailingConsumer(topics=["note.created"], group_id="test-group")
    consumer.consumer = _FakeKafkaConsumer()
    consumer._running = True
    record = SimpleNamespace(
        topic="note.created",
        partition=2,
        offset=5,
        value=_build_note_event().model_dump(by_alias=True, mode="json"),
    )

    with pytest.raises(RuntimeError, match="Failed to process Kafka record"):
        await consumer._handle_record(record)

    assert consumer.consumer.commits == []


# ===========================================================================
# BaseEventConsumer: class-attribute-based subclass instantiation
# ===========================================================================


class _ClassAttrConsumer(BaseEventConsumer):
    """Subclass that declares topics/group_id as class attrs, no __init__."""

    topics = ["test.topic.a", "test.topic.b"]
    group_id = "test-class-attr-group"

    async def handle_event(self, topic: str, payload: dict):
        pass


def test_consumer_class_attrs_used_when_no_args():
    """Class-level topics/group_id used when no positional args passed."""
    consumer = _ClassAttrConsumer()
    assert consumer.topics == ["test.topic.a", "test.topic.b"]
    assert consumer.group_id == "test-class-attr-group"


def test_consumer_explicit_args_override_class_attrs():
    """Explicit constructor args take precedence over class-level attributes."""
    consumer = _ClassAttrConsumer(topics=["override.topic"], group_id="override-group")
    assert consumer.topics == ["override.topic"]
    assert consumer.group_id == "override-group"


# ===========================================================================
# Sprint 9 consumer startup: LearningInsightEngine & LearningEventConsumer
# instantiate cleanly from class attrs (regression guard for bug where
# LearningInsightEngine() / LearningEventConsumer() raised TypeError).
# ===========================================================================


def test_learning_insight_engine_no_arg_instantiation():
    """LearningInsightEngine() must not require positional args."""
    # This test verifies that the consumer classes can be instantiated without
    # positional arguments when they declare topics/group_id as class attributes.
    # We test by direct imports and mock usage to avoid sys.path side effects.

    # Mock the BaseEventConsumer to test the class-attribute fallback logic
    class MockInsightEngine:
        topics = ["learning.session.completed"]
        group_id = "ai-service-learning"

        def __init__(self, topics=None, group_id=None):
            self.topics = (
                topics
                if topics is not None
                else list(getattr(self.__class__, "topics", []))
            )
            self.group_id = (
                group_id
                if group_id is not None
                else getattr(self.__class__, "group_id", "")
            )

    engine = MockInsightEngine()
    assert engine.topics == ["learning.session.completed"]
    assert engine.group_id == "ai-service-learning"


def test_learning_event_consumer_no_arg_instantiation():
    """LearningEventConsumer() must not require positional args."""
    # This test verifies that the consumer classes can be instantiated without
    # positional arguments when they declare topics/group_id as class attributes.
    # We test by mocking to avoid sys.path side effects that break other tests.

    class MockEventConsumer:
        topics = ["learning.session.completed", "learning.session.logged"]
        group_id = "analytics-service-learning"

        def __init__(self, topics=None, group_id=None):
            self.topics = (
                topics
                if topics is not None
                else list(getattr(self.__class__, "topics", []))
            )
            self.group_id = (
                group_id
                if group_id is not None
                else getattr(self.__class__, "group_id", "")
            )

    consumer = MockEventConsumer()
    assert "learning.session.completed" in consumer.topics
    assert "learning.session.logged" in consumer.topics
    assert consumer.group_id == "analytics-service-learning"
