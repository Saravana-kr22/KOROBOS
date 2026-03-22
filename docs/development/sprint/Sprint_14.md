# KOROBOS — Sprint 14 Execution Plan

## Knowledge Graph System (Web + Android React Native Support)

Version: 1.0
Owner: Saravana Perumal

---

# 1. Sprint Objective

Sprint 14 introduces the **Knowledge Graph System**, enabling KOROBOS to represent relationships between all user data as a connected graph.

This system powers:

- Note linking (Second Brain)
- Cross-domain relationships (habits, learning, health, DB records)
- Contextual insights
- Graph visualization (web + mobile)
- AI reasoning layer (future)

---

# 2. Core Goals

The Knowledge Graph must:

- represent entities as nodes
- represent relationships as edges
- support real-time updates
- enable graph queries
- integrate with Notes, DB, Learning, Health
- support mobile graph visualization

---

# 3. Architecture Overview

        Client (Web / React Native)
        ↓
        API Gateway
        ↓
        Graph Service
        ↓
        Graph Database (Neo4j / PostgreSQL Graph)
        ↓
        Event Bus
        ↓
        Source Services

---

# 4. Technology Stack

Backend: FastAPI\
Graph DB: Neo4j (recommended) / PostgreSQL (adjacency list)\
Cache: Redis\
Event Bus: Kafka

Frontend Web: React (Graph visualization libs)\
Frontend Mobile: React Native (lightweight graph view)

---

# 5. Service Structure

backend/services/graph-service/

        app/
            main.py
            api/graph_routes.py
            services/graph_service.py
            services/node_service.py
            services/edge_service.py
            repositories/graph_repository.py
            schemas/graph_schema.py
            events/graph_events.py
            config/settings.py

        workers/
            graph_worker.py

        Dockerfile
        requirements.txt

---

# 6. Core Concepts

Nodes = Entities\
Edges = Relationships

---

# 7. Node Types

Supported node types:

note\
habit\
learning_topic\
health_log\
database_record

---

# 8. Edge Types

Relationships:

note_links\
habit_related_to_learning\
learning_related_to_note\
health_related_to_habit\
record_related_to_note

---

# 9. Graph Schema

Node:

        id UUID
        type TEXT
        title TEXT
        metadata JSON

Edge:

        source_id UUID
        target_id UUID
        relation_type TEXT

---

# 10. Graph Creation Flow

        User creates/updates data
        ↓
        Service emits event
        ↓
        Graph Worker consumes event
        ↓
        Create/update nodes
        ↓
        Create/update edges

---

# 11. Example

Note: Machine Learning\
Note: Deep Learning

Edge:

Machine Learning → Deep Learning

---

# 12. API Endpoints

GET /graph/node/{id}\
GET /graph/neighbors/{id}\
GET /graph/subgraph?node_id=...

---

# 13. Subgraph Retrieval

Used for UI visualization.

Returns:

- nodes
- edges

---

# 14. Mobile Support (React Native)

Mobile graph features:

- lightweight graph rendering
- node tap interaction
- limited node expansion
- pagination of neighbors

---

# 15. Graph Visualization

Web:

- full graph view
- zoom + pan
- clustering

Mobile:

- simplified graph
- focus view

---

# 16. Event Integration

Events consumed:

note.link.created\
record.created\
habit.created\
learning.session.completed

---

# 17. Graph Queries

Supported queries:

- find related notes
- find connected habits
- find knowledge clusters

---

# 18. Caching

Redis caching:

- node neighbors
- subgraphs

TTL: 5 minutes

---

# 19. Security

- JWT authentication
- user graph isolation

---

# 20. Rate Limiting

Graph APIs:

50 requests/min/user

---

# 21. Observability

Metrics:

- graph size
- query latency
- node/edge creation rate

Tools:

Prometheus
Grafana

---

# 22. Testing Strategy

Tests:

- node creation tests
- edge creation tests
- graph query tests
- API tests

---

# 23. Sprint Validation Checklist

✔ nodes created correctly\
✔ edges created correctly\
✔ graph queries working\
✔ subgraph API working\
✔ mobile graph supported\
✔ event-driven updates working

---

# Final Outcome

After Sprint 14 KOROBOS provides:

- fully connected knowledge graph
- cross-domain relationships
- graph-based navigation
- foundation for AI reasoning

This completes the **graph intelligence layer**, enabling KOROBOS to act as a true **connected knowledge system**.
