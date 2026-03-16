# KOROBOS — Sprint 7 Execution Plan

## Structured Database System (Web + Android React Native Support)

Version: 1.0
Owner: Saravana Perumal

---

# 1. Sprint Objective

Sprint 7 introduces the **Structured Database System** for KOROBOS.

This feature allows users to create **Notion-style structured databases** inside the platform.
The system supports:

- custom database tables
- dynamic properties (fields)
- multiple views (table / kanban / calendar)
- filtering and sorting
- structured records connected to knowledge notes
- mobile-friendly interaction for Android React Native

This sprint establishes the **data modeling layer** for KOROBOS beyond simple notes.

---

# 2. System Goals

The structured database system must allow users to:

- create custom databases
- define fields dynamically
- insert records
- edit records
- link records to notes
- visualize records using different views
- query records with filters

Supported clients:

- Web (React / Next.js)
- Android (React Native)
- Future iOS apps

---

# 3. Architecture Overview

        Client (Web / React Native)
        ↓
        API Gateway
        ↓
        Database Service
        ↓
        PostgreSQL
        ↓
        Event Bus
        ↓
        Consumers
            - Analytics Service
            - AI Service
            - Search Indexer

---

# 4. Core Components

Structured Database System consists of:

- Database Definition Engine
- Field / Property Engine
- Record Management System
- View Rendering System
- Query Engine
- Event Publishing System

---

# 5. Technology Stack

Backend Framework: FastAPI
Database: PostgreSQL
ORM: SQLAlchemy
Migration Tool: Alembic
Cache: Redis
Event Streaming: Kafka

Frontend (Web): React / Next.js
Frontend (Mobile): React Native

---

# 6. Service Directory Structure

backend/services/database-service/

        app/
            main.py
            api/
                database_routes.py
            services/
                database_service.py
                record_service.py
                query_engine.py
            repositories/
                database_repository.py
                record_repository.py
                property_repository.py
            models/
                database_model.py
                property_model.py
                record_model.py
            schemas/
                database_schema.py
            events/
                database_events.py
            config/
                settings.py

        Dockerfile
        requirements.txt

---

# 7. Core Data Model

The system supports dynamic schemas.

Key entities:

- databases
- properties
- records
- record values

---

# 8. Database Schema

Table: databases

        id UUID
        user_id UUID
        name TEXT
        created_at TIMESTAMP

---

Table: properties

        id UUID
        database_id UUID
        name TEXT
        type TEXT

Property types:

        text
        number
        boolean
        date
        select
        multi-select
        relation

---

Table: records

        id UUID
        database_id UUID
        created_at TIMESTAMP

---

Table: record_values

        record_id UUID
        property_id UUID
        value TEXT

---

# 9. Property Types

Supported property types:

        Text
        Number
        Boolean
        Date
        Select
        Multi-Select
        Relation (link to another record)

These types must be supported in both Web and React Native UI.

---

# 10. Record Creation Flow

        User creates record
        ↓
        API request
        ↓
        Database Service validates schema
        ↓
        Insert record
        ↓
        Insert property values
        ↓
        Publish event

---

# 11. Record Editing Flow

        User edits record
        ↓
        API request
        ↓
        Update property values
        ↓
        Update timestamps
        ↓
        Publish update event

---

# 12. Query Engine

The query engine supports:

Filtering

Example:

        status = "In Progress"

Sorting

Example:

        order by created_at desc

Pagination

Example:

        ?page=1&limit=20

---

# 13. Views System

Supported database views:

        Table View
        Kanban View
        Calendar View

---

## Table View

Standard spreadsheet style display.

        Columns = properties
        Rows = records

---

## Kanban View

Records grouped by select property.

Example:

        TODO | IN PROGRESS | DONE

---

## Calendar View

Records displayed based on date property.

Used for planning and scheduling.

---

# 14. Mobile Support (React Native)

Mobile apps must support:

- viewing database records
- creating records
- editing records
- switching views
- filtering data

Mobile API usage must minimize payload size.

---

# 15. API Endpoints

POST /databases
GET /databases
GET /databases/{id}

POST /databases/{id}/properties

POST /databases/{id}/records
GET /databases/{id}/records

PUT /records/{id}
DELETE /records/{id}

---

Example Create Database Request

```json
{
  "name": "Project Tasks"
}
```

---

Example Create Record Request

```json
{
  "title": "Build Auth Service",
  "status": "In Progress"
}
```

---

# 16. Relations Between Records

Relation properties allow linking records.

Example:

        Task → Project

Relation stored using property type "relation".

---

# 17. Integration with Notes

Records can reference notes.

Example:

        Task record links to a knowledge note.

This enables structured knowledge management.

---

# 18. Event Publishing

Events emitted:

        database.created
        record.created
        record.updated
        record.deleted

---

Example Event

```json
{
  "event_type": "record.created",
  "payload": {
    "database_id": "...",
    "record_id": "..."
  }
}
```

---

# 19. Search Integration

Record events trigger search indexing.

Pipeline:

        Event Bus
        ↓
        Search Worker
        ↓
        Meilisearch

---

# 20. AI Integration

Structured data improves AI insights.

Examples:

        task progress analysis
        productivity insights
        learning tracking

Events feed AI service.

---

# 21. Caching Strategy

Redis caching used for:

        database metadata
        recent queries

Cache TTL: 5 minutes

---

# 22. Security

Security checks:

        validate JWT identity
        verify database ownership
        sanitize inputs

---

# 23. Rate Limiting

Write operations limited.

Example:

        30 record updates per minute.

---

# 24. Observability

Metrics tracked:

        database creation rate
        record creation rate
        query latency

Monitoring tools:

        Prometheus
        Grafana

---

# 25. Testing Strategy

Tests required:

        database creation tests
        property creation tests
        record CRUD tests
        query engine tests

Tools:

        pytest
        httpx
        pytest-asyncio

---

# 26. Sprint Validation Checklist

✔ database creation working
✔ property creation working
✔ record CRUD operations working
✔ query engine filtering working
✔ table view functional
✔ kanban view functional
✔ calendar view functional
✔ mobile clients supported
✔ events emitted correctly

---

# Final Sprint Outcome

After Sprint 7 KOROBOS will have a **fully functional structured database system** supporting:

- dynamic tables
- custom fields
- multiple views
- structured records
- mobile interaction
- event-driven analytics

This feature transforms KOROBOS into a **hybrid knowledge + structured data platform** similar to Notion-style databases integrated with a Second Brain system.
