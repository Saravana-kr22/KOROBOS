# KOROBOS — Sprint 13 Execution Plan

## Unified Search System (Web + Android React Native Support)

Version: 1.0
Owner: Saravana Perumal

---

# 1. Sprint Objective

Sprint 13 introduces the **Unified Search System**, enabling users to search across all KOROBOS data:

- Notes (Markdown knowledge)
- Structured Databases
- Habits
- Learning Sessions
- Health Logs

This system provides **fast, relevant, and cross-domain search** with support for:

• full-text search
• semantic search (future-ready)
• filtering and ranking
• mobile-friendly responses

---

# 2. Core Goals

The search system must:

- index all domain data
- support fast queries (<200ms)
- provide ranked results
- support filters (type, date, tags)
- support mobile lightweight queries
- integrate with event-driven updates

---

# 3. Architecture Overview

        Client (Web / React Native)
        ↓
        API Gateway
        ↓
        Search Service
        ↓
        Search Engine (Meilisearch)
        ↓
        Event Bus
        ↓
        Data Sources (Notes, DB, Habit, Learning, Health)

---

# 4. Technology Stack

Search Engine: Meilisearch\
Backend: FastAPI\
Cache: Redis\
Event Bus: Kafka

Future Enhancement: Vector DB (for semantic search)

---

# 5. Service Structure

backend/services/search-service/

        app/
            main.py
            api/search_routes.py
            services/search_service.py
            services/indexing_service.py
            repositories/search_repository.py
            schemas/search_schema.py
            events/search_events.py
            config/settings.py

        workers/
        search_index_worker.py

        Dockerfile
        requirements.txt

---

# 6. Index Design

Single unified index OR multiple indexes:

Option A: unified_index\
Option B: notes_index, habits_index, learning_index, health_index

Recommended: **Hybrid approach**

---

# 7. Indexed Fields

Notes:

- title
- content_md
- tags

Habits:

- name
- description

Learning:

- topic
- notes

Health:

- food_name
- workout_type

---

# 8. Search Flow

        User enters query
        ↓
        API Gateway
        ↓
        Search Service
        ↓
        Search Engine query
        ↓
        Rank + filter results
        ↓
        Return response

---

# 9. API Endpoints

GET /search?q=keyword\
GET /search/advanced

---

Example Response:

```json
{
  "results": [
    {
      "type": "note",
      "title": "Machine Learning",
      "snippet": "Deep learning is..."
    }
  ]
}
```

---

# 10. Mobile Support (React Native)

Mobile features:

- instant search suggestions
- lightweight responses
- pagination
- offline cached queries

---

# 11. Event-Driven Indexing

Events consumed:

note.created\
note.updated\
record.created\
habit.created\
learning.session.logged\
meal.logged

---

# 12. Indexing Pipeline

        Event Bus
        ↓
        Search Worker
        ↓
        Transform data
        ↓
        Update Meilisearch index

---

# 13. Ranking Strategy

Ranking factors:

- text relevance
- recency
- frequency of access

---

# 14. Filters

Supported filters:

- type (note, habit, learning)
- date range
- tags

---

# 15. Caching

Redis caching:

- frequent queries
- autocomplete suggestions

TTL: 2 minutes

---

# 16. Autocomplete

Support search suggestions:

GET /search/suggest?q=mach

Returns:

Machine Learning\
Machine Vision

---

# 17. Security

- JWT authentication
- user-specific filtering

---

# 18. Rate Limiting

Search API:

200 requests/min/user

---

# 19. Observability

Metrics:

- search latency
- query volume
- result accuracy

Tools:

Prometheus\
Grafana

---

# 20. Testing Strategy

Tests:

- search accuracy
- ranking validation
- API tests
- indexing tests

---

# 21. Sprint Validation Checklist

✔ search working across all domains\
✔ indexing pipeline working\
✔ ranking accurate\
✔ filters working\
✔ mobile search optimized\
✔ autocomplete working

---

# Final Outcome

After Sprint 13 KOROBOS provides:

- unified search across all data
- fast and relevant results
- mobile-optimized search
- event-driven indexing

This completes the **information retrieval layer** of KOROBOS, enabling users to quickly access any data across the platform.
