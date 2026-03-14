# KOROBOS – Enterprise LLD Template
Document Name: Cache Architecture Low Level Design
Project: KOROBOS – Second Brain Operating System
Version: 1.0
Author: Saravana Perumal K
Date: 2026-03-07
Status: Draft

## 1. Overview
### 1.1 Purpose
Improves system responsiveness and reduces database load through distributed caching.

## 2. Technology
* **Provider**: Redis.

## 3. Caching Strategy
| Cache Category | TTL | Key Format |
| :--- | :--- | :--- |
| Dashboard Data | 5 min | `dash:{user_id}:{view}` |
| User Session | 24 hour | `sess:{token_id}` |
| Analytics Insights | 30 min | `stats:{user_id}` |
