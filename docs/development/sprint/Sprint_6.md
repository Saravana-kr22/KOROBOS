# KOROBOS — Sprint 6 Execution Plan

## Notes & Knowledge Service (Web + Android React Native Support)

Version: 1.0
Owner: Saravana Perumal K

---

# 1. Sprint Objective

Sprint 6 implements the **Notes & Knowledge Service**, which forms the core of the KOROBOS "Second Brain" system.

This service enables users to:

- create markdown notes
- edit and store knowledge
- link notes using wiki-style links
- build a knowledge graph
- search knowledge content
- generate events for analytics, AI, and search systems

The system must support:

- Web client (React / Next.js)
- Android mobile app (React Native)
- API integrations
- Event-driven processing

This sprint builds the **knowledge layer of KOROBOS**.

---

# 2. Service Responsibilities

The Notes & Knowledge Service is responsible for:

- note creation
- note editing
- note deletion
- note retrieval
- markdown storage
- wiki-link detection
- backlink generation
- knowledge graph relationships
- tag management
- search indexing events
- publishing domain events

---

# 3. Architecture Overview

        Client (Web / Android React Native)
        ↓
        API Gateway
        ↓
        Notes Service
        ↓
        PostgreSQL Database
        ↓
        Event Bus
        ↓
        Consumers
            - Search Indexer
            - Graph Engine
            - AI Service
            - Analytics Service

---

# 4. Technology Stack

Backend:

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- Kafka Event Bus

Search:

- Meilisearch

Graph Processing:

- Graph Worker

---

# 5. Service Directory Structure

backend/services/notes-service/

        app/
            main.py
            api/
                notes_routes.py
            services/
                notes_service.py
                link_parser.py
            repositories/
                notes_repository.py
                link_repository.py
            models/
                note_model.py
                link_model.py
                tag_model.py
            schemas/
                note_schema.py
            events/
                notes_events.py
            config/
                settings.py

        Dockerfile
        requirements.txt

---

# 6. Database Schema

Table: notes

| Column     | Type      |
| ---------- | --------- |
| id         | UUID      |
| user_id    | UUID      |
| title      | TEXT      |
| content_md | TEXT      |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

---

Table: note_links

| Column         | Type |
| -------------- | ---- |
| source_note_id | UUID |
| target_note_id | UUID |

---

Table: tags

| Column | Type |
| ------ | ---- |
| id     | UUID |
| name   | TEXT |

---

Table: note_tags

| Column  | Type |
| ------- | ---- |
| note_id | UUID |
| tag_id  | UUID |

---

# 7. Markdown Storage

Notes are stored in **Markdown format**.

Example:

# Machine Learning

Deep learning is a subset of [Artificial Intelligence].

Benefits:

- simple text format
- easy editing
- compatible with mobile apps
- portable knowledge storage

---

# 8. Wiki-Link Detection

The system must detect links in markdown.

Example:

[[Machine Learning]]
[[Deep Learning]]

Parser logic:

1 scan markdown text
2 detect link patterns
3 create relationships
4 update note_links table

---

# 9. Backlink Generation

Backlinks show which notes reference the current note.

Example:

Deep Learning note:

Backlinks:

Machine Learning
Neural Networks

Backlinks calculated using note_links table.

---

# 10. Knowledge Graph Generation

Nodes:

notes

Edges:

note_links

Graph engine consumes events and updates graph database.

Graph used for visualization in frontend.

---

# 11. API Endpoints

POST /notes
GET /notes/{note_id}
GET /notes
PUT /notes/{note_id}
DELETE /notes/{note_id}

---

Example Create Note Request

```json
{
  "title": "Machine Learning",
  "content_md": "Introduction to ML"
}
```

---

Example Response

```json
{
  "id": "uuid",
  "title": "Machine Learning",
  "created_at": "timestamp"
}
```

---

# 12. Mobile Support (React Native)

Mobile features:

- markdown editor support
- offline draft support
- sync via API

Mobile workflow:

        User edits note → send API request → backend stores markdown → response returned.

---

# 13. Note Editing Flow

        User edits note
        ↓
        API request
        ↓
        Notes Service validates input
        ↓
        Update database
        ↓
        Parse wiki-links
        ↓
        Emit events
        ↓
        Return response

---

# 14. Event Publishing

Events emitted by Notes Service:

note.created
note.updated
note.deleted
note.link.created

---

Example Event

```json
{
  "event_type": "note.created",
  "timestamp": "ISO8601",
  "payload": {
    "note_id": "..."
  }
}
```

---

# 15. Search Index Pipeline

        Event Bus
        ↓
        Search Worker
        ↓
        Meilisearch Index

Allows full-text search across notes.

---

# 16. Knowledge Graph Pipeline

        Event Bus
        ↓
        Graph Worker
        ↓
        Graph Database

Used for visualization of knowledge network.

---

# 17. AI Pipeline

        Event Bus
        ↓
        AI Service
        ↓
        Embedding Generation
        ↓
        Vector Database

Enables:

- note summarization
- knowledge insights

---

# 18. Caching Strategy

Use Redis caching for:

- recent notes
- dashboard queries

Cache TTL:

5 minutes

---

# 19. Pagination

Large note lists must support pagination.

        GET /notes?page=1&limit=20

---

# 20. Security

Security checks:

- user must own note
- validate JWT identity
- sanitize markdown

---

# 21. Rate Limiting

Write operations limited.

Example:

        50 note edits per minute.

---

# 22. Observability

Metrics:

- note creation rate
- edit frequency
- search queries

Monitoring:

Prometheus
Grafana

---

# 23. Testing Strategy

Tests required:

- create note tests
- edit note tests
- wiki-link parsing tests
- API integration tests

Tools:

pytest
httpx
pytest-asyncio

---

# 24. Sprint Validation Checklist

✔ note creation working
✔ note editing working
✔ note retrieval working
✔ wiki-links detected
✔ backlinks generated
✔ events emitted correctly
✔ search indexing working
✔ graph updates working
✔ mobile clients supported

---

# Final Sprint Outcome

After Sprint 6 the KOROBOS platform will have a **fully operational knowledge management system**.

Capabilities:

- markdown note system
- knowledge linking
- backlinks
- knowledge graph generation
- search indexing
- event-driven knowledge processing

This forms the **core of the Second Brain architecture**.
