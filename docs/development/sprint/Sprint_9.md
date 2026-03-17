# KOROBOS — Sprint 9 Execution Plan

## Learning Tracking System (Web + Android React Native Support)

Version: 1.0
Owner: Saravana Perumal

---

# 1. Sprint Objective

Sprint 9 introduces the **Learning Tracking System**, enabling users to track, measure, and improve their learning activities.

This system transforms KOROBOS into a **continuous learning platform** integrated with:

- Notes (knowledge system)
- Structured databases
- Habit tracking
- AI insights

Capabilities delivered:

- track learning sessions
- log study time and topics
- connect learning to notes
- measure learning progress
- generate analytics & insights
- support mobile logging (React Native Android)
- event-driven learning analytics

---

# 2. Supported Clients

The system must support:

- Web (React / Next.js)
- Android Mobile (React Native)
- Future iOS
- API integrations

Mobile users must be able to:

- log learning sessions
- start/stop timers
- view learning stats
- connect sessions to notes
- review progress dashboards

---

# 3. Architecture Overview

        Client (Web / React Native)
        ↓
        API Gateway
        ↓
        Learning Service
        ↓
        PostgreSQL
        ↓
        Event Bus
        ↓
        Consumers

            Analytics Service
            AI Service
            Search Service

---

# 4. Core Components

Learning Tracking System consists of:

- Learning Session Engine
- Timer Engine
- Topic/Subject Management
- Learning Analytics Engine
- Integration with Notes
- Event Publishing System

---

# 5. Technology Stack

Backend: FastAPI\
Database: PostgreSQL\
ORM: SQLAlchemy\
Migration: Alembic\
Cache: Redis\
Event Bus: Kafka

Frontend Web: React / Next.js\
Frontend Mobile: React Native

---

# 6. Service Directory Structure

backend/services/learning-service/

        app/
            main.py
            api/learning_routes.py
            services/learning_service.py
            services/timer_service.py
            services/analytics_service.py
            repositories/session_repository.py
            repositories/topic_repository.py
            models/session_model.py
            models/topic_model.py
            schemas/learning_schema.py
            events/learning_events.py
            config/settings.py

        Dockerfile
        requirements.txt

---

# 7. Core Entities

- learning_sessions
- topics
- session_notes

---

# 8. Database Schema

Table: topics

        id UUID
        user_id UUID
        name TEXT
        created_at TIMESTAMP

---

Table: learning_sessions

        id UUID
        user_id UUID
        topic_id UUID
        start_time TIMESTAMP
        end_time TIMESTAMP
        duration_minutes INT
        notes TEXT

---

Table: session_notes (link to knowledge system)

        session_id UUID
        note_id UUID

---

# 9. Learning Session Flow

        User starts session
        ↓
        Timer starts
        ↓
        User studies
        ↓
        User stops session
        ↓
        Session stored
        ↓
        Event published

---

# 10. Timer Engine

Supports:

- start session
- pause session
- resume session
- stop session

Mobile support:

- background timer support
- offline session tracking

---

# 11. Session Logging

Users can log sessions manually:

Example:

```json
{
  "topic": "Machine Learning",
  "duration_minutes": 60
}
```

---

# 12. Topic Management

Users can:

- create topics
- edit topics
- delete topics

Topics group learning sessions.

---

# 13. Integration with Notes

Learning sessions can link to notes.

Example:

Learning session → [[Deep Learning Notes]]

Enables knowledge-based learning tracking.

---

# 14. API Endpoints

POST /learning/topics
GET /learning/topics

POST /learning/session/start
POST /learning/session/stop
POST /learning/session/log

GET /learning/sessions
GET /learning/stats

---

# 15. Mobile Support (React Native)

Mobile features:

- start/stop learning timer
- offline session tracking
- quick logging
- push reminders
- session history view

Mobile must support:

- background timer persistence
- sync after reconnect

---

# 16. Learning Analytics

Metrics calculated:

- total learning time
- sessions per day
- topic distribution
- learning streak
- weekly progress

---

# 17. Event Publishing

Events generated:

learning.session.started
learning.session.completed
learning.topic.created

Example:

```json
{
  "event_type": "learning.session.completed",
  "payload": {
    "session_id": "...",
    "duration": 60
  }
}
```

---

# 18. Analytics Pipeline

        Event Bus
        ↓
        Analytics Worker
        ↓
        Aggregation
        ↓
        Analytics DB
        ↓
        Dashboard APIs

---

# 19. AI Insights

AI Service uses events to generate:

- learning recommendations
- optimal study times
- knowledge gaps
- productivity insights

---

# 20. Caching Strategy

Redis caching used for:

- recent sessions
- dashboard stats

Cache TTL: 2 minutes

---

# 21. Security

Security checks:

- JWT authentication
- user ownership validation
- input validation

---

# 22. Rate Limiting

Example:

30 session logs per minute

---

# 23. Observability

Metrics:

- session creation rate
- total learning time
- API latency

Monitoring:

Prometheus
Grafana

---

# 24. Testing Strategy

Tests required:

- session start/stop tests
- timer accuracy tests
- analytics tests
- API integration tests

Tools:

pytest
httpx
pytest-asyncio

---

# 25. Sprint Validation Checklist

✔ session start/stop working
✔ manual session logging working
✔ topic management working
✔ mobile timer working
✔ offline sync working
✔ analytics working
✔ events emitted correctly
✔ integration with notes working

---

# Final Sprint Outcome

After Sprint 9 KOROBOS supports:

- learning session tracking
- topic-based learning organization
- mobile learning tracking
- learning analytics
- AI-powered learning insights

This Sprint completes the **learning intelligence layer** of KOROBOS, making it a **knowledge + behavior + learning platform**.
