# KOROBOS — Sprint 8 Execution Plan

## Habit Tracking System (Web + Android React Native Support)

Version: 1.0
Owner: Saravana Perumal

---

# 1. Sprint Objective

Sprint 8 introduces the **Habit Tracking System** enabling KOROBOS users to build, track, and analyze habits.

Capabilities:

- Habit creation
- Habit scheduling (daily / weekly / custom)
- Habit completion logging
- Streak calculation
- Habit reminders
- Analytics insights
- Android React Native support
- Event-driven processing

---

# 2. Supported Clients

- Web (React / Next.js)
- Android (React Native)
- Future iOS
- API integrations

Mobile users must be able to:

- create habits
- mark habits complete
- see streaks
- receive reminders
- view habit statistics

---

# 3. Architecture

Client (Web / React Native)
↓
API Gateway
↓
Habit Service
↓
PostgreSQL
↓
Event Bus
↓
Consumers

Analytics Service
Notification Service
AI Service

---

# 4. Technology Stack

Backend: FastAPI
Database: PostgreSQL
ORM: SQLAlchemy
Migration: Alembic
Cache: Redis
Event Bus: Kafka

Frontend Web: React / Next.js
Frontend Mobile: React Native

---

# 5. Service Structure

backend/services/habit-service/

        app/
            main.py
            api/habit_routes.py
            services/habit_service.py
            services/streak_service.py
            services/schedule_service.py
            repositories/habit_repository.py
            repositories/habit_log_repository.py
            models/habit_model.py
            models/habit_log_model.py
            models/habit_schedule_model.py
            schemas/habit_schema.py
            events/habit_events.py
            config/settings.py

            Dockerfile
            requirements.txt

---

# 6. Core Entities

- habits
- habit_schedules
- habit_logs

---

# 7. Database Schema

Table: habits

        id UUID
        user_id UUID
        name TEXT
        description TEXT
        created_at TIMESTAMP
        is_active BOOLEAN

Table: habit_schedules

        id UUID
        habit_id UUID
        frequency TEXT
        days_of_week TEXT
        time_of_day TIME

Table: habit_logs

        id UUID
        habit_id UUID
        completed_at TIMESTAMP
        status BOOLEAN

---

# 8. Habit Creation Flow

        User creates habit
        ↓
        API request
        ↓
        validate input
        ↓
        store habit
        ↓
        store schedule
        ↓
        emit event

---

# 9. Habit Completion Flow

        User marks habit complete
        ↓
        API request
        ↓
        insert habit_log
        ↓
        update streak
        ↓
        publish event

---

# 10. Streak Calculation

Streak Service calculates:

- current_streak
- longest_streak

Missed day resets streak.

---

# 11. Habit Scheduling

Supported schedules:

- Daily
- Weekly
- Custom

Schedule engine determines today's habits.

---

# 12. Reminder Pipeline

        Habit schedule
        ↓
        Reminder Scheduler
        ↓
        Notification Service
        ↓
        Push Notification

---

# 13. Mobile Support (React Native)

Mobile features:

- Habit dashboard
- Quick completion
- Streak display
- Push reminders
- Offline completion sync

---

# 14. Habit Dashboard API

    GET /habits/today

Example response:

```
[
 { "habit_id": "...", "name": "Workout", "completed": false }
]
```

---

# 15. API Endpoints

POST /habits
GET /habits
GET /habits/{id}
POST /habits/{id}/complete
GET /habits/today
GET /habits/{id}/stats

---

# 16. Habit Analytics

Analytics metrics:

- completion rate
- current streak
- longest streak
- weekly consistency

Events sent to Analytics Service.

---

# 17. Event Publishing

Events:
habit.created
habit.completed
habit.streak.updated

Example:

```json
{
  "event_type": "habit.completed",
  "payload": { "habit_id": "...", "user_id": "..." }
}
```

---

# 18. AI Insights

AI Service analyzes:

- habit success patterns
- optimal schedules
- behavior insights

---

# 19. Caching

Redis used for:

- today's habits
- habit statistics

Cache TTL: 2 minutes

---

# 20. Security

- JWT authentication
- habit ownership validation
- input sanitization

---

# 21. Rate Limiting

Example:
20 habit completions per minute.

---

# 22. Observability

Metrics:

- habit creation rate
- completion rate
- API latency

Monitoring:
Prometheus
Grafana

---

# 23. Testing

Tests:

- habit creation
- completion
- streak logic
- schedule engine

Tools:
pytest
httpx
pytest-asyncio

---

# 24. Sprint Validation Checklist

- habit creation working
- completion logging working
- streak calculation working
- schedules functioning
- today dashboard working
- mobile clients supported
- events emitted correctly
- analytics pipeline working

---

# Final Sprint Outcome

After Sprint 8 KOROBOS supports:

- habit creation
- streak tracking
- daily dashboards
- mobile habit tracking
- analytics and AI insights

This completes the **behavior tracking layer** of KOROBOS.
