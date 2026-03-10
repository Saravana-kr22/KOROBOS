"""
CortexOS event schema registry.

Loads event definitions from `schemas/events/` and validates event payloads
before they are published to Kafka.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from backend.shared.messaging.schemas import BaseEvent


class EventSchemaError(ValueError):
    """Base exception for schema registry failures."""


class EventSchemaNotFoundError(EventSchemaError):
    """Raised when no schema file exists for an event type."""


class EventValidationError(EventSchemaError):
    """Raised when an event does not conform to its registered schema."""


@dataclass(frozen=True)
class PayloadFieldSchema:
    """Single payload field definition loaded from schema JSON."""

    type: str
    items: Optional[str] = None
    nullable: bool = False


@dataclass(frozen=True)
class EventSchemaDefinition:
    """Schema metadata for a single event type."""

    event_type: str
    schema_version: int
    required_payload_fields: tuple[str, ...]
    payload_properties: dict[str, PayloadFieldSchema]
    allow_additional_payload: bool
    partition_key: Optional[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _schema_dir() -> Path:
    return _repo_root() / "schemas" / "events"


def _schema_filename(event_type: str) -> str:
    return f"{event_type.replace('.', '_')}.json"


def _load_schema_from_path(path: Path) -> EventSchemaDefinition:
    raw = json.loads(path.read_text(encoding="utf-8"))
    payload_properties = {
        field_name: PayloadFieldSchema(
            type=field_schema["type"],
            items=field_schema.get("items"),
            nullable=field_schema.get("nullable", False),
        )
        for field_name, field_schema in raw.get("payload_properties", {}).items()
    }
    return EventSchemaDefinition(
        event_type=raw["event_type"],
        schema_version=raw.get("schema_version", 1),
        required_payload_fields=tuple(raw.get("required_payload_fields", [])),
        payload_properties=payload_properties,
        allow_additional_payload=raw.get("allow_additional_payload", True),
        partition_key=raw.get("partition_key"),
    )


@lru_cache(maxsize=None)
def get_event_schema(event_type: str) -> EventSchemaDefinition:
    schema_path = _schema_dir() / _schema_filename(event_type)
    if schema_path.exists():
        return _load_schema_from_path(schema_path)

    if event_type.endswith(".dlq"):
        dlq_schema = _schema_dir() / "__dlq__.json"
        if dlq_schema.exists():
            return _load_schema_from_path(dlq_schema)

    raise EventSchemaNotFoundError(
        f"No schema registered for event_type '{event_type}'"
    )


def infer_partition_key(
    event: BaseEvent, schema: Optional[EventSchemaDefinition] = None
) -> Optional[str]:
    """Infer the preferred Kafka partition key for an event."""
    schema = schema or get_event_schema(event.event_type)
    if not schema.partition_key:
        return None
    value = event.payload.get(schema.partition_key)
    if value is None:
        return None
    return str(value)


def validate_event(event: BaseEvent) -> EventSchemaDefinition:
    """Validate an event instance against the registered schema definition."""
    schema = get_event_schema(event.event_type)

    if event.schema_version != schema.schema_version:
        raise EventValidationError(
            "Schema version mismatch for "
            f"{event.event_type}: got {event.schema_version}, "
            f"expected {schema.schema_version}"
        )

    missing_fields = [
        field_name
        for field_name in schema.required_payload_fields
        if field_name not in event.payload
    ]
    if missing_fields:
        raise EventValidationError(
            f"{event.event_type} is missing required payload field(s): "
            f"{', '.join(missing_fields)}"
        )

    if not schema.allow_additional_payload:
        unknown_fields = sorted(set(event.payload) - set(schema.payload_properties))
        if unknown_fields:
            raise EventValidationError(
                f"{event.event_type} contains unsupported payload field(s): "
                f"{', '.join(unknown_fields)}"
            )

    for field_name, value in event.payload.items():
        field_schema = schema.payload_properties.get(field_name)
        if field_schema is None:
            continue
        _validate_payload_field(event.event_type, field_name, value, field_schema)

    return schema


def _validate_payload_field(
    event_type: str,
    field_name: str,
    value: Any,
    field_schema: PayloadFieldSchema,
) -> None:
    if value is None:
        if field_schema.nullable:
            return
        raise EventValidationError(f"{event_type}.{field_name} cannot be null")

    if field_schema.type == "string":
        if not isinstance(value, str):
            raise EventValidationError(f"{event_type}.{field_name} must be a string")
        return

    if field_schema.type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise EventValidationError(f"{event_type}.{field_name} must be an integer")
        return

    if field_schema.type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise EventValidationError(f"{event_type}.{field_name} must be a number")
        return

    if field_schema.type == "boolean":
        if not isinstance(value, bool):
            raise EventValidationError(f"{event_type}.{field_name} must be a boolean")
        return

    if field_schema.type == "object":
        if not isinstance(value, dict):
            raise EventValidationError(f"{event_type}.{field_name} must be an object")
        return

    if field_schema.type == "array":
        if not isinstance(value, list):
            raise EventValidationError(f"{event_type}.{field_name} must be an array")
        if field_schema.items is None:
            return
        for item in value:
            _validate_payload_field(
                event_type,
                f"{field_name}[]",
                item,
                PayloadFieldSchema(type=field_schema.items),
            )
        return

    raise EventValidationError(
        f"{event_type}.{field_name} uses unsupported schema type '{field_schema.type}'"
    )
