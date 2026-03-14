# KOROBOS – Enterprise LLD Template
Document Name: Event Architecture Low Level Design
Project: KOROBOS – Second Brain Operating System
Version: 1.0
Author: Saravana Perumal K
Date: 2026-03-07
Status: Draft

## 1. Overview
### 1.1 Purpose
Defines the asynchronous communication backbone using an EventBus to decouple services.

## 2. Architecture
### 2.1 Event Flow
* Services publish events → EventBus routes to topics → Analytics/Search/AI consume.

## 3. Core Event Topics
| Topic | Source Service | Consumer(s) |
| :--- | :--- | :--- |
| note.created | Notes Service | Search, AI, Graph |
| habit.completed | Habit Service | Analytics, Dashboard |

## 4. Payload Standard
```json
{
 "event_type": "string",
 "timestamp": "ISO8601",
 "data": { "key": "value" }
}
```
