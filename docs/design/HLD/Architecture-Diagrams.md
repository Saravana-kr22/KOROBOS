# KOROBOS -- Architecture Diagram

Version: 1.0 \
Owner: Saravana Perumal K \
Project: KOROBOS -- Second Brain Operating System

------------------------------------------------------------------------

# Architecture Overview

```mermaid
flowchart TB

User --> API

API --> Services

Services --> EventBus

EventBus --> Analytics
EventBus --> Notifications
EventBus --> AI
EventBus --> Search
EventBus --> GraphEngine
EventBus --> Dashboard
```

------------------------------------------------------------------------

# C4 Architecture diagrams

## System Context Diagram

```mermaid
flowchart TB

User[User / Knowledge Worker]

Browser[Web App]
Mobile[Mobile App]

PKM[Second Brain Platform]

Auth[Auth Provider]
Email[Email Service]
AI[AI Model Provider]
Storage[Cloud Storage]

User --> Browser
User --> Mobile

Browser --> PKM
Mobile --> PKM

PKM --> Auth
PKM --> Email
PKM --> AI
PKM --> Storage
```

------------------------------------------------------------------------

## Container Diagram

```mermaid 
flowchart TB

subgraph Client
Web[React Web App]
Mobile[React Native App]
end

subgraph Backend
API[API Gateway]
AuthService[Auth Service]
NotesService[Notes Service]
HabitService[Habit Service]
LearningService[Learning Service]
AnalyticsService[Analytics Service]
NotificationService[Notification Service]
AIService[AI Service]
end

subgraph Data
Postgres[(PostgreSQL)]
Redis[(Redis Cache)]
Search[(Search Index)]
ObjectStore[(Object Storage)]
end

Web --> API
Mobile --> API

API --> AuthService
API --> NotesService
API --> HabitService
API --> LearningService
API --> AnalyticsService
API --> NotificationService
API --> AIService

NotesService --> Postgres
HabitService --> Postgres
LearningService --> Postgres

API --> Redis

NotesService --> Search
NotesService --> ObjectStore
```

------------------------------------------------------------------------

## Component Diagram (Notes Service)

```mermaid 
flowchart TB

API[Notes API]

Editor[Markdown Editor Engine]
LinkEngine[Bidirectional Link Engine]
GraphEngine[Knowledge Graph Builder]
IndexEngine[Search Indexer]

DB[(Notes Table)]
Search[(Search Engine)]

API --> Editor
Editor --> DB

API --> LinkEngine
LinkEngine --> DB

API --> GraphEngine
GraphEngine --> DB

API --> IndexEngine
IndexEngine --> Search
```

------------------------------------------------------------------------

# Complete Database ER Diagram

```mermaid
erDiagram

USERS {
uuid user_id
string email
timestamp created_at
}

NOTES {
uuid note_id
uuid user_id
string title
text content_md
timestamp created_at
}

NOTE_LINKS {
uuid source_note
uuid target_note
}

TAGS {
uuid tag_id
string name
}

NOTE_TAGS {
uuid note_id
uuid tag_id
}

HABITS {
uuid habit_id
uuid user_id
string name
string frequency
}

HABIT_LOGS {
uuid log_id
uuid habit_id
date log_date
boolean completed
}

LEARNING_SESSIONS {
uuid session_id
uuid user_id
string topic
int duration
timestamp created_at
}

EXERCISES {
uuid exercise_id
uuid user_id
string workout_type
int duration
}

MEALS {
uuid meal_id
uuid user_id
int calories
}

USERS ||--o{ NOTES : owns
USERS ||--o{ HABITS : creates
USERS ||--o{ LEARNING_SESSIONS : logs
USERS ||--o{ EXERCISES : tracks
USERS ||--o{ MEALS : logs

NOTES ||--o{ NOTE_LINKS : links
NOTES ||--o{ NOTE_TAGS : tagged

HABITS ||--o{ HABIT_LOGS : records
```

------------------------------------------------------------------------

# Microservice Architecture Map

```mermaid
flowchart TB

Gateway[API Gateway]

Auth[Auth Service]
Notes[Notes Service]
Habits[Habit Service]
Learning[Learning Service]
Health[Health Service]
Analytics[Analytics Service]
Notifications[Notification Service]
AI[AI Service]

Gateway --> Auth
Gateway --> Notes
Gateway --> Habits
Gateway --> Learning
Gateway --> Health
Gateway --> Analytics
Gateway --> Notifications
Gateway --> AI

Notes --> Analytics
Habits --> Analytics
Learning --> Analytics
Health --> Analytics
```

------------------------------------------------------------------------

# Realtime Collaboration Architecture

```mermaid
flowchart TB

UserA
UserB
UserC

Editor[Collaborative Editor]

WebSocket[Realtime Sync Server]

CRDT[CRDT Engine]

DB[(Document Store)]

UserA --> Editor
UserB --> Editor
UserC --> Editor

Editor --> WebSocket
WebSocket --> CRDT
CRDT --> DB
```

------------------------------------------------------------------------

# Event Flow Architecture

## Global Event Flow Architecture

```mermaid
flowchart LR

User --> API

API --> NotesService
API --> HabitService
API --> LearningService
API --> HealthService
API --> DashboardService

NotesService --> EventBus
HabitService --> EventBus
LearningService --> EventBus
HealthService --> EventBus

EventBus --> AnalyticsService
EventBus --> SearchIndexer
EventBus --> NotificationService
EventBus --> AIService
EventBus --> DashboardService
```

------------------------------------------------------------------------

## Knowledge Vault Event Flow

```mermaid
sequenceDiagram

participant User
participant API
participant NotesService
participant EventBus
participant SearchIndexer
participant GraphEngine
participant AIService
participant Dashboard

User->>API: Create/Edit Note
API->>NotesService: Save Markdown
NotesService->>EventBus: note_created

EventBus->>SearchIndexer: index_note
EventBus->>GraphEngine: update_graph
EventBus->>AIService: generate_summary
EventBus->>Dashboard: refresh_widgets
```

------------------------------------------------------------------------

## Note Linking Event Flow

```mermaid
sequenceDiagram

participant Editor
participant NotesService
participant EventBus
participant GraphEngine
participant Search

Editor->>NotesService: Add [[link]]
NotesService->>EventBus: note_link_created

EventBus->>GraphEngine: update_edges
EventBus->>Search: update_index
```

------------------------------------------------------------------------

## Habit Tracking Event Flow

```mermaid
sequenceDiagram

participant User
participant API
participant HabitService
participant EventBus
participant Analytics
participant Notification
participant Dashboard

User->>API: Mark Habit Complete
API->>HabitService: Save Habit Log

HabitService->>EventBus: habit_completed

EventBus->>Analytics: update_streak
EventBus->>Dashboard: refresh_habit_widget
EventBus->>Notification: schedule_next_reminder
```

------------------------------------------------------------------------

## Learning Tracker Event Flow

```mermaid
sequenceDiagram

participant User
participant API
participant LearningService
participant EventBus
participant Analytics
participant AI
participant Dashboard

User->>API: Log Learning Session
API->>LearningService: Save Session

LearningService->>EventBus: learning_session_logged

EventBus->>Analytics: update_learning_stats
EventBus->>AI: analyze_skill_progress
EventBus->>Dashboard: update_learning_widget
```

------------------------------------------------------------------------

## Health Tracking Event Flow

```mermaid
sequenceDiagram

participant User
participant API
participant HealthService
participant EventBus
participant Analytics
participant Dashboard

User->>API: Log Meal
API->>HealthService: Save Meal

HealthService->>EventBus: meal_logged

EventBus->>Analytics: update_calorie_stats
EventBus->>Dashboard: update_health_widget
```

------------------------------------------------------------------------

## Exercise Tracking Event Flow

```mermaid
sequenceDiagram

participant User
participant API
participant HealthService
participant EventBus
participant Analytics
participant Dashboard

User->>API: Log Workout
API->>HealthService: Save Workout

HealthService->>EventBus: workout_logged

EventBus->>Analytics: update_exercise_stats
EventBus->>Dashboard: refresh_widget
```

------------------------------------------------------------------------

## Dashboard Widget Update Flow

```mermaid
sequenceDiagram

participant EventBus
participant DashboardService
participant Cache
participant UI

EventBus->>DashboardService: new_activity_event
DashboardService->>Cache: update_widget_data
DashboardService->>UI: push_update
```

------------------------------------------------------------------------

## Notification Event Flow

```mermaid
sequenceDiagram

participant EventBus
participant NotificationService
participant Scheduler
participant Email
participant Push

EventBus->>NotificationService: habit_completed
NotificationService->>Scheduler: schedule_next_reminder

Scheduler->>Push: send_notification
Scheduler->>Email: send_email
```

------------------------------------------------------------------------

## Analytics Engine Event Flow

```mermaid
sequenceDiagram

participant EventBus
participant AnalyticsService
participant DataWarehouse
participant Dashboard

EventBus->>AnalyticsService: activity_event
AnalyticsService->>DataWarehouse: store_metrics
AnalyticsService->>Dashboard: update_insights
```

------------------------------------------------------------------------

## Search Indexing Pipeline

```mermaid
sequenceDiagram

participant EventBus
participant SearchIndexer
participant SearchEngine

EventBus->>SearchIndexer: note_created
SearchIndexer->>SearchEngine: update_index
```

------------------------------------------------------------------------

## Knowledge Graph Update Flow

```mermaid
sequenceDiagram

participant EventBus
participant GraphService
participant GraphDB
participant UI

EventBus->>GraphService: note_link_created
GraphService->>GraphDB: update_relationship
GraphService->>UI: refresh_graph
```

------------------------------------------------------------------------

## AI Insight Pipeline

```mermaid
sequenceDiagram

participant EventBus
participant AIService
participant VectorDB
participant LLM
participant Dashboard

EventBus->>AIService: knowledge_event
AIService->>VectorDB: store_embedding
AIService->>LLM: generate_insight
AIService->>Dashboard: show_recommendation
```

------------------------------------------------------------------------

## Daily Insight Generation Flow

```mermaid
sequenceDiagram

participant Scheduler
participant Analytics
participant AI
participant Dashboard

Scheduler->>Analytics: aggregate_daily_metrics
Analytics->>AI: send_behavior_data
AI->>Dashboard: generate_daily_insights
```

------------------------------------------------------------------------

# AI Pipeline Architecture

```mermaid
flowchart TB

UserInput[User Note / Data]

Preprocess[Text Preprocessing]

Embedding[Embedding Generator]

VectorDB[(Vector Database)]

Retriever[Semantic Retriever]

LLM[LLM Engine]

Insight[Insight Generator]

UserInput --> Preprocess
Preprocess --> Embedding
Embedding --> VectorDB

Retriever --> VectorDB
Retriever --> LLM

LLM --> Insight
Insight --> Dashboard
```
