# KOROBOS Complete API Documentation

Version: 1.0 \
Owner: Saravana Perumal K

Base URL: /api/v1

Authentication: JWT Bearer Token

Authorization Header: Authorization: Bearer `<token>`{=html}

------------------------------------------------------------------------

# 1. Authentication APIs

## Signup

POST /auth/signup

Request

        { "email": "user@example.com", "password": "password123" }

Response

        { "user_id": "uuid", "email": "user@example.com", "created_at":
        "timestamp" }

------------------------------------------------------------------------

## Login

POST /auth/login

Request

        { "email": "user@example.com", "password": "password123" }

Response

        { "access_token": "jwt", "refresh_token": "jwt", "token_type": "bearer"
        }

------------------------------------------------------------------------

## Refresh Token

POST /auth/refresh

Request

        { "refresh_token": "jwt" }

Response

        { "access_token": "new_jwt" }

------------------------------------------------------------------------

# 2. Notes APIs

## Create Note

POST /notes

Request

        { "title": "Machine Learning", "content_md": "Introduction to ML" }

Response

        { "id": "uuid", "title": "Machine Learning", "content_md": "Introduction
        to ML", "created_at": "timestamp" }

------------------------------------------------------------------------

## Get Note

GET /notes/{note_id}

Response

        { "id": "uuid", "title": "Machine Learning", "content_md": "...",
        "created_at": "timestamp" }

------------------------------------------------------------------------

## List Notes

GET /notes

Response

    [ { "id": "uuid", "title": "ML", "created_at": "timestamp" }]

------------------------------------------------------------------------

## Delete Note

DELETE /notes/{note_id}

Response

    { "status": "deleted" }

------------------------------------------------------------------------

# 3. Habit APIs

## Create Habit

POST /habits

Request

    { "name": "Workout", "frequency": "daily" }

Response

    { "id": "uuid", "name": "Workout", "frequency": "daily" }

------------------------------------------------------------------------

## List Habits

GET /habits

Response

    [ { "id": "uuid", "name": "Workout", "frequency": "daily" }]

------------------------------------------------------------------------

## Complete Habit

POST /habits/{habit_id}/complete

Response

    { "habit_id": "uuid", "completed": true, "streak": 14 }

------------------------------------------------------------------------

## Habit Analytics

GET /habits/analytics

Response

    { "completion_rate": 82, "current_streak": 14 }

------------------------------------------------------------------------

# 4. Learning APIs

## Log Learning Session

POST /learning-session

Request

    { "topic": "System Design", "duration": 120 }

Response

    { "session_id": "uuid", "topic": "System Design", "duration": 120 }

------------------------------------------------------------------------

## Get Learning Stats

GET /learning-stats

Response

    { "total_hours": 120, "topics": \["AI","System Design"\] }

------------------------------------------------------------------------

# 5. Health APIs

## Log Meal

POST /health/meal

Request

    { "calories": 500 }

Response

    { "meal_id": "uuid", "calories": 500 }

------------------------------------------------------------------------

## Log Workout

POST /health/workout

Request

    { "workout_type": "Running", "duration": 30, "calories_burned": 300 }

Response

    { "workout_id": "uuid", "duration": 30 }

------------------------------------------------------------------------

## Health Stats

GET /health/stats

Response

    { "daily_calories": 2000, "workout_minutes": 45 }

------------------------------------------------------------------------

# 6. Analytics APIs

## Productivity Score

GET /analytics/productivity

Response

    { "score": 82 }

------------------------------------------------------------------------

## Habit Trends

GET /analytics/habit-trends

Response

    { "weekly_consistency": 75 }

------------------------------------------------------------------------

## Learning Growth

GET /analytics/learning-growth

Response

    { "weekly_hours": 12 }

------------------------------------------------------------------------

# 7. Notifications APIs

## Get Notifications

GET /notifications

Response

    [ { "id": "uuid", "message": "Workout reminder" }]

------------------------------------------------------------------------

## Mark Notification Read

POST /notifications/read

Request

    { "notification_id": "uuid" }

Response

    { "status": "read" }

------------------------------------------------------------------------

# 8. AI APIs

## Summarize Note

POST /ai/summarize-note

Request

    { "note_id": "uuid" }

Response

    { "summary": "Short AI generated summary" }

------------------------------------------------------------------------

## Get AI Insights

GET /ai/insights

Response

{ "insights": \[ "You studied more this week", "Maintain habit streak"
\] }

------------------------------------------------------------------------

# 9. Dashboard APIs

## Daily Dashboard

GET /dashboard/daily

Response

    { "habit_completion": 80, "learning_hours": 3, "calories": 2000 }

------------------------------------------------------------------------

## Weekly Dashboard

GET /dashboard/weekly

Response

    { "habit_consistency": 75, "learning_hours": 12 }

------------------------------------------------------------------------

# 10. Error Response Format

All APIs return standard errors

    { "error": { "code": "RESOURCE_NOT_FOUND", "message": "Note not found" }
    }

------------------------------------------------------------------------

# Final API Vision

The KOROBOS API layer exposes all platform capabilities through a
unified REST interface.

Key characteristics

-   RESTful endpoints
-   JWT authentication
-   Event driven backend
-   Microservice modular design