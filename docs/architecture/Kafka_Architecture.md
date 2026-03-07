# CortexOS Kafka Event Streaming Architecture

Version: 1.0 \
Owner: Saravana Perumal K

------------------------------------------------------------------------

# 1. Overview

CortexOS uses **Apache Kafka** as the central event streaming platform
to enable asynchronous communication between microservices.

Kafka allows services to publish events without tightly coupling to
other services.

Benefits:

-   Event driven architecture
-   High throughput event processing
-   Scalable microservice communication
-   Reliable message delivery
-   Real‑time analytics pipelines

------------------------------------------------------------------------

# 2. Kafka Architecture

    Microservices
         ↓
    Kafka Producers
         ↓
    Kafka Cluster (Brokers)
         ↓
    Kafka Topics
         ↓
    Kafka Consumers
         ↓
    Analytics / AI / Notifications / Search

------------------------------------------------------------------------

# 3. Kafka Components

## Kafka Brokers

Kafka cluster contains multiple brokers.

Responsibilities:

-   store event logs
-   manage partitions
-   replicate data for fault tolerance

Example cluster

    Broker 1
    Broker 2
    Broker 3

------------------------------------------------------------------------

## Kafka Topics

Topics are event streams where producers send messages.

Example topics used in CortexOS:

  Topic                     Description
  ------------------------- -------------------
  note.created              New note created
  note.link.created         Notes linked
  habit.completed           Habit finished
  learning.session.logged   Learning activity
  meal.logged               Meal recorded
  workout.logged            Workout activity

------------------------------------------------------------------------

## Partitions

Each topic contains partitions to allow parallel processing.

Example

    Topic: note.created

    Partition 0
    Partition 1
    Partition 2

Benefits:

-   horizontal scaling
-   parallel consumer processing

------------------------------------------------------------------------

# 4. Event Producers

Services publishing events.

  Service            Produced Events
  ------------------ -----------------------------
  Notes Service      note.created
  Habit Service      habit.completed
  Learning Service   learning.session.logged
  Health Service     meal.logged, workout.logged
  Auth Service       user.created

Example producer flow

    API Request
       ↓
    Service Logic
       ↓
    Kafka Producer
       ↓
    Publish Event to Topic

------------------------------------------------------------------------

# 5. Event Consumers

Services subscribing to events.

  Consumer               Consumed Events
  ---------------------- ---------------------
  Analytics Service      all activity events
  Notification Service   habit.completed
  AI Service             note.created
  Search Indexer         note.created

Consumer flow

    Kafka Topic
       ↓
    Consumer Group
       ↓
    Process Event
       ↓
    Update Service

------------------------------------------------------------------------

# 6. Consumer Groups

Multiple consumers can read from a topic.

Example

    Topic: habit.completed

    Consumer Group: analytics-service
    Consumer Group: notification-service

Benefits:

-   load balancing
-   fault tolerance

------------------------------------------------------------------------

# 7. Event Flow Example

## Note Creation Flow

    User creates note
          ↓
    Notes Service
          ↓
    Kafka Producer
          ↓
    Topic: note.created
          ↓
    Consumers:
        Analytics Service
        AI Service
        Search Indexer

------------------------------------------------------------------------

# 8. Event Schema Design

Example event payload

Topic: note.created

``` json
{
  "event_id": "uuid",
  "event_type": "note.created",
  "timestamp": "2026-01-01T10:00:00Z",
  "user_id": "uuid",
  "note_id": "uuid",
  "title": "Machine Learning"
}
```

------------------------------------------------------------------------

# 9. Topic Naming Convention

Standard topic naming pattern

    <domain>.<event>

Examples

    note.created
    note.updated
    habit.completed
    learning.session.logged
    health.workout.logged

------------------------------------------------------------------------

# 10. Partition Strategy

Partition key examples

  Topic                     Partition Key
  ------------------------- ---------------
  note.created              user_id
  habit.completed           habit_id
  learning.session.logged   user_id

Benefits

-   ordered processing per entity
-   balanced partition distribution

------------------------------------------------------------------------

# 11. Retention Policy

Kafka stores events for a configurable duration.

Example configuration

    Retention: 7 days
    Cleanup Policy: delete

Long term analytics events may be stored longer.

------------------------------------------------------------------------

# 12. Exactly Once Processing

Strategies

-   idempotent producers
-   consumer offset tracking
-   transactional writes

Ensures reliable analytics processing.

------------------------------------------------------------------------

# 13. Dead Letter Queue

Failed messages are redirected to DLQ topics.

Example

    note.created.dlq
    habit.completed.dlq

Used for debugging and reprocessing.

------------------------------------------------------------------------

# 14. Kafka Security

Security mechanisms

-   TLS encryption
-   SASL authentication
-   ACL authorization

Example

    Producer Auth → Kafka Broker
    Consumer Auth → Kafka Broker

------------------------------------------------------------------------

# 15. Monitoring Kafka

Monitoring tools

-   Prometheus
-   Grafana
-   Kafka Exporter

Key metrics

-   message throughput
-   consumer lag
-   broker health

------------------------------------------------------------------------

# 16. Deployment Architecture

Kafka cluster deployed inside Kubernetes.

    Kubernetes Cluster
          ↓
    Kafka StatefulSet
          ↓
    Persistent Volumes

Recommended operators

-   Strimzi Kafka Operator

------------------------------------------------------------------------

# 17. Scaling Strategy

Scaling options

-   increase topic partitions
-   add consumer instances
-   add Kafka brokers

Target throughput

    100k+ events per second

------------------------------------------------------------------------

# 18. CortexOS Kafka Topic Map

  Topic                     Producer           Consumers
  ------------------------- ------------------ --------------------------
  note.created              Notes Service      AI, Analytics
  note.link.created         Notes Service      Graph Service
  habit.completed           Habit Service      Analytics, Notifications
  learning.session.logged   Learning Service   Analytics
  meal.logged               Health Service     Analytics
  workout.logged            Health Service     Analytics

------------------------------------------------------------------------

# Final Architecture Vision

Kafka enables CortexOS to operate as a **real‑time intelligence
platform**.

Key characteristics

-   asynchronous microservices
-   real time analytics
-   AI event pipelines
-   scalable event streaming