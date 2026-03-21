# 1. Sprint Objective

Sprint 11 introduces the **Dashboard Aggregation Service**, which acts as the **central intelligence layer** of KOROBOS.

This service aggregates data from all core systems:

- Authentication
- Notes & Knowledge
- Structured Databases
- Habit Tracking
- Learning Tracking
- Health Tracking

The goal is to provide:

• unified dashboard
• cross-domain insights
• real-time and aggregated metrics
• AI-ready data layer
• mobile-friendly dashboards (React Native Android)

---

# 2. Core Responsibilities

Dashboard Aggregation Service is responsible for:

- aggregating data across services
- computing derived metrics
- building dashboard APIs
- caching aggregated responses
- supporting real-time updates
- enabling personalized dashboards

---

# 3. Architecture Overview

        Client (Web / React Native)
        ↓
        API Gateway
        ↓
        Dashboard Service
        ↓
        Cache Layer (Redis)
        ↓
        Aggregated Data Store (PostgreSQL / OLAP)
        ↓
        Event Bus
        ↓
        Data Sources (Habit, Learning, Health, Notes)

---

# 4. Data Sources

Dashboard pulls data from:

- Habit Service (streaks, completions)
- Learning Service (sessions, time spent)
- Health Service (calories, workouts)
- Notes Service (activity, growth)
- Database Service (records, tasks)

---

# 5. Aggregation Types

Real-Time Aggregation:

- current day stats
- live habit completion

Batch Aggregation:

- weekly summaries
- monthly trends

Precomputed Metrics:

- productivity score
- consistency score

---

# 6. Technology Stack

Backend: FastAPI\
Database: PostgreSQL / OLAP (ClickHouse optional)\
Cache: Redis\
Event Bus: Kafka

---

# 7. Service Directory Structure

backend/services/dashboard-service/

        app/
            main.py
            api/dashboard_routes.py
            services/dashboard_service.py
            services/aggregation_engine.py
            services/metric_engine.py
            repositories/dashboard_repository.py
            models/dashboard_model.py
            schemas/dashboard_schema.py
            events/dashboard_events.py
            config/settings.py

        Dockerfile
        requirements.txt

---

# 8. Core Metrics

Daily Metrics:

- habits completed
- learning time
- calories consumed/burned

Weekly Metrics:

- habit consistency
- learning growth
- health balance

---

# 9. Productivity Score

Composite score based on:

- habit completion
- learning activity
- health balance

Example formula:

score = (habit*score * 0.4) + (learning*score * 0.3) + (health_score \* 0.3)

---

# 10. Dashboard APIs

GET /dashboard/overview\
GET /dashboard/daily\
GET /dashboard/weekly\
GET /dashboard/metrics

---

Example Response

```json
{
  "date": "2026-01-01",
  "habits_completed": 5,
  "learning_minutes": 60,
  "calories_balance": 1500,
  "productivity_score": 78
}
```

---

# 11. Mobile Support (React Native)

Mobile dashboard must support:

- summary cards
- charts (lightweight data)
- pull-to-refresh
- offline cached view

APIs must return **optimized payloads**.

---

# 12. Aggregation Engine

Aggregation engine processes:

- incoming events
- historical data queries

Supports:

- incremental updates
- batch recomputation

---

# 13. Event-Driven Updates

Dashboard updates triggered by events:

habit.completed
learning.session.completed
meal.logged

---

# 14. Caching Strategy

Redis caching:

- dashboard overview
- daily stats

TTL:

1–5 minutes

---

# 15. Data Storage Strategy

Two storage layers:

1. Raw data (source services)
2. Aggregated data (dashboard DB)

---

# 16. Personalization

User-specific dashboards:

- preferred metrics
- custom widgets (future)

---

# 17. Security

- JWT authentication
- user-specific data isolation

---

# 18. Rate Limiting

Dashboard API:

100 requests/minute per user

---

# 19. Observability

Metrics:

- API latency
- aggregation time
- cache hit rate

Tools:

Prometheus
Grafana

---

# 20. Testing Strategy

Tests:

- aggregation accuracy tests
- API response tests
- caching tests

Tools:

pytest
httpx

---

# 21. Sprint Validation Checklist

✔ dashboard overview working
✔ daily metrics working
✔ weekly metrics working
✔ productivity score correct
✔ mobile dashboard working
✔ caching working
✔ event-driven updates working

---

# Final Outcome

After Sprint 11 KOROBOS provides:

- unified dashboard
- cross-domain insights
- productivity scoring
- mobile-friendly dashboards

This sprint completes the **aggregation and visualization layer**, enabling KOROBOS to act as a true **intelligent personal operating system**.
