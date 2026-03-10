# CortexOS --- Sprint 4 Execution Plan

## Event Bus Infrastructure

Version: 1.0 \
Owner: Saravana Perumal

------------------------------------------------------------------------

# 1. Sprint Objective

Sprint 4 establishes the **Event Bus Infrastructure** that enables
asynchronous communication between CortexOS microservices.

CortexOS backend is built on an **event‑driven architecture**, allowing
services to communicate through events instead of direct calls.

Benefits:

-   loose coupling between services
-   scalable background processing
-   analytics pipeline triggers
-   AI insight generation
-   notification workflows

After Sprint 4 completion the platform will support:

✔ distributed event streaming\
✔ asynchronous microservice communication\
✔ event‑driven analytics pipeline\
✔ notification processing pipeline\
✔ AI insight triggers

------------------------------------------------------------------------

# 2. Event Driven Architecture Overview

CortexOS services communicate using **events published to an event
bus**.

Architecture flow:

User Action\
↓\
API Gateway\
↓\
Domain Service\
↓\
Event Bus\
↓\
Consumers

Consumers include:

-   Analytics Service
-   Notification Service
-   AI Service
-   Search Indexer
-   Knowledge Graph Engine
-   Dashboard Aggregator

------------------------------------------------------------------------

# 3. Event Bus Technology

Recommended Event Streaming Platform:

**Apache Kafka**

Alternatives:

-   NATS
-   RabbitMQ

Kafka advantages:

-   high throughput
-   horizontal scalability
-   event persistence
-   partitioning
-   consumer replay capability

------------------------------------------------------------------------

# 4. Event Bus Infrastructure Components

Core components:

-   Kafka Brokers
-   Zookeeper (or KRaft mode)
-   Kafka Topics
-   Producer Clients
-   Consumer Groups
-   Schema Registry
-   Event Workers

------------------------------------------------------------------------

# 5. Kafka Cluster Architecture

Production cluster:

    kafka-cluster/
        broker-1
        broker-2
        broker-3

Recommended configuration:

-   replication factor = 3
-   multiple partitions per topic
-   persistent storage

Development cluster:

Single broker using Docker.

------------------------------------------------------------------------

# 6. Local Development Setup

Add Kafka services to docker-compose.

Example:

services:

kafka: image: bitnami/kafka ports: - "9092:9092"

zookeeper: image: bitnami/zookeeper

Environment variable:

KAFKA_BROKER=localhost:9092

------------------------------------------------------------------------

# 7. Topic Design

Topics follow **domain-driven design**.

Core topics:

  Topic                     Description
  ------------------------- -------------------
  note.created              new note created
  note.updated              note edited
  note.link.created         note linking
  habit.created             new habit
  habit.completed           habit completed
  learning.session.logged   learning activity
  meal.logged               food logged
  workout.logged            workout logged

------------------------------------------------------------------------

# 8. Event Naming Convention

Events follow this format:

    <domain>.<action>

Examples:

note.created\
habit.completed\
learning.session.logged\
health.meal.logged

------------------------------------------------------------------------

# 9. Event Schema Standard

All events must follow a consistent schema.

Example:

{ "event_id": "uuid", "event_type": "note.created", "timestamp":
"ISO8601", "producer": "notes-service", "payload": {} }

Fields:

event_id → unique event identifier\
event_type → event name\
timestamp → event time\
producer → source service\
payload → event data

------------------------------------------------------------------------

# 10. Schema Registry

Schema registry manages event definitions.

Responsibilities:

-   store event schemas
-   enforce compatibility
-   validate payloads

Schema location:

schemas/events/

Example:

note_created.json

------------------------------------------------------------------------

# 11. Producer Library

Shared Kafka producer must be implemented.

Location:

backend/shared/messaging/

Features:

-   event publishing
-   retry mechanism
-   idempotency
-   schema validation

Example usage:

publish_event("note.created", payload)

------------------------------------------------------------------------

# 12. Consumer Framework

Consumers process events asynchronously.

Worker directory:

backend/workers/

Example workers:

-   analytics_worker
-   notification_worker
-   search_worker
-   ai_worker

------------------------------------------------------------------------

# 13. Consumer Groups

Consumer groups allow parallel event processing.

Example groups:

analytics-group\
notification-group\
ai-group

Each group processes events independently.

------------------------------------------------------------------------

# 14. Event Processing Example

Example: Note Creation

User creates note\
↓\
Notes Service saves note\
↓\
Notes Service emits **note.created**\
↓\
Event Bus receives event\
↓\
Consumers process event

Consumers:

Analytics Service → update metrics\
Search Worker → update search index\
Graph Worker → update graph\
AI Worker → generate summary

------------------------------------------------------------------------

# 15. Event Replay

Kafka supports replaying historical events.

Use cases:

-   rebuild analytics
-   rebuild search index
-   regenerate AI insights

Replay implemented via consumer offsets.

------------------------------------------------------------------------

# 16. Partition Strategy

Partitions allow scalable throughput.

Recommended partition keys:

user_id\
note_id\
habit_id

Ensures ordering per entity.

------------------------------------------------------------------------

# 17. Dead Letter Queue

Failed messages must be redirected to DLQ.

DLQ topics:

note.created.dlq\
habit.completed.dlq

Used for debugging and recovery.

------------------------------------------------------------------------

# 18. Retry Strategy

Retry policy:

Attempt 1 → immediate\
Attempt 2 → 5 seconds\
Attempt 3 → 30 seconds

After failure → send to DLQ.

------------------------------------------------------------------------

# 19. Background Workers

Workers process heavy workloads.

Workers include:

Analytics Worker\
Search Worker\
Notification Worker\
AI Worker

Workers consume Kafka topics.

------------------------------------------------------------------------

# 20. Analytics Pipeline

Event Flow:

Event Bus\
↓\
Analytics Worker\
↓\
Metrics Aggregation\
↓\
Analytics Database\
↓\
Dashboard APIs

Generated metrics:

-   productivity score
-   habit consistency
-   learning growth

------------------------------------------------------------------------

# 21. Notification Pipeline

Event Flow:

Event Bus\
↓\
Notification Worker\
↓\
Notification Scheduler\
↓\
Push / Email

Example:

habit.completed → schedule reminder

------------------------------------------------------------------------

# 22. AI Insight Pipeline

Event Flow:

Event Bus\
↓\
AI Worker\
↓\
Embedding Generation\
↓\
Vector Database\
↓\
LLM Insight Engine

Insights displayed in dashboard.

------------------------------------------------------------------------

# 23. Search Index Pipeline

Event Flow:

Event Bus\
↓\
Search Worker\
↓\
Meilisearch Index Update

------------------------------------------------------------------------

# 24. Knowledge Graph Pipeline

Event Flow:

Event Bus\
↓\
Graph Worker\
↓\
Graph Database Update

Used for knowledge graph visualization.

------------------------------------------------------------------------

# 25. Monitoring

Kafka must be monitored.

Metrics:

-   topic throughput
-   consumer lag
-   failed messages

Tools:

Prometheus\
Grafana

------------------------------------------------------------------------

# 26. Security

Security controls:

-   TLS encryption
-   SASL authentication
-   Kafka ACL rules

Only authorized services can produce/consume events.

------------------------------------------------------------------------

# 27. Event Versioning

Events must support schema evolution.

Example:

note.created.v1\
note.created.v2

Consumers must remain backward compatible.

------------------------------------------------------------------------

# 28. Testing Strategy

Required tests:

-   producer tests
-   consumer tests
-   integration tests
-   contract tests

Tools:

pytest\
testcontainers

Kafka integration tests are expected to run from the backend Poetry
environment with Docker available, for example:

`poetry run pytest tests/test_messaging_integration.py`

------------------------------------------------------------------------

# 29. Sprint Validation Checklist

Before sprint completion verify:

✔ Kafka cluster operational\
✔ Topics created\
✔ Producer library functional\
✔ Consumer framework operational\
✔ Events successfully published\
✔ Events consumed by workers\
✔ DLQ functioning\
✔ Schema validation working\
✔ Monitoring dashboards available

------------------------------------------------------------------------

# Final Sprint Outcome

After Sprint 4 the CortexOS platform will have a **fully operational
event‑driven backbone**.

All services will communicate through events.

This enables:

-   scalable analytics pipelines
-   AI insight generation
-   asynchronous workflows
-   reliable background processing

The platform is now ready for **core domain service implementation and
real data processing**.
