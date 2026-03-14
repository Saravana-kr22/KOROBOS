# KOROBOS – Enterprise LLD Template
Document Name: Learning Service Low Level Design
Project: KOROBOS – Second Brain Operating System
Version: 1.0
Author: Saravana Perumal K
Date: 2026-03-07
Status: Draft

## 1. Overview
### 1.1 Purpose
The Learning Service tracks skill development through session logging and topic mastery tracking.

### 1.2 Scope
**In Scope**
* Logging learning sessions (duration, topic, notes).
* Skill progress tracking and mastery calculation.
**Out of Scope**
* External course integration APIs.

### 1.3 Dependencies
| Dependency | Purpose |
| :--- | :--- |
| PostgreSQL | Persistence for learning sessions. |
| EventBus | Publishing logs for analytics and AI. |

## 2. Architecture
### 2.1 Component Overview
Learning API → Session Manager → Progress Calculator → Event Publisher.

## 3. Data Model
### 3.1 Tables
**Learning_Sessions Table**
| Column | Type | Description |
| :--- | :--- | :--- |
| session_id | UUID | PK |
| user_id | UUID | Owner |
| topic | String | Skill topic |
| duration | Int | Minutes spent |
| created_at | Timestamp | Log time |

## 4. API Design
### 4.1 Log Session
`POST /api/v1/learning-session`
### 4.2 Get Stats
`GET /api/v1/learning-stats`

## 5. Event Architecture
### 5.1 Events Published
| Event | Description |
| :--- | :--- |
| learning_session_logged | Triggered when a new session is saved. |

## 6. Observability
* **Metrics**: `learning_hours_total`, `skill_mastery_index`.
