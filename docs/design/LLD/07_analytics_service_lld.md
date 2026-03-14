# KOROBOS – Enterprise LLD Template
Document Name: Analytics Service Low Level Design
Project: KOROBOS – Second Brain Operating System
Version: 1.0
Author: Saravana Perumal K
Date: 2026-03-07
Status: Draft

## 1. Overview
### 1.1 Purpose
Transforms raw tracking data into actionable insights, productivity scores, and growth trends.

### 1.2 Scope
**In Scope**
* Calculation of habit consistency scores.
* Productivity trend analysis.
* Learning growth metrics.

### 1.3 Dependencies
| Dependency | Purpose |
| :--- | :--- |
| EventBus | Consuming activity events from all services. |
| Data Warehouse | Long-term metric storage (e.g., ClickHouse). |

## 2. Architecture
### 2.1 Component Overview
Event Consumer → Metric Processor → Data Warehouse → Insights API.

## 3. Internal Logic
### 3.1 Habit Consistency Calculation
* Logic: `(completed_days / total_days) * 100` over a rolling 7-day window.

## 4. Event Architecture
### 4.1 Events Consumed
* `note.created`, `habit.completed`, `learning_session_logged`, `meal_logged`.

## 5. Observability
* **Metrics**: `productivity_score`, `user_engagement_rate`.
