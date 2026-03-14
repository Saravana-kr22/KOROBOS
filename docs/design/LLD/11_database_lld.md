# KOROBOS – Enterprise LLD Template
Document Name: Global Database Low Level Design
Project: KOROBOS – Second Brain Operating System
Version: 1.0
Author: Saravana Perumal K
Date: 2026-03-07
Status: Draft

## 1. Overview
### 1.1 Purpose
Defines the centralized relational schema for all persistent data across the KOROBOS ecosystem.

## 2. Architecture
### 2.1 Technology Stack
* Primary: PostgreSQL.
* Secondary: Redis (Cache).

## 3. Data Model (ER Diagram Summary)

* **Core Entity**: `USERS` table links to all tracking logs.
* **Relational Links**: `NOTES` table connects to `NOTE_LINKS` and `NOTE_TAGS`.
* **Tracking Links**: `HABITS` table records daily progress in `HABIT_LOGS`.

## 4. Performance Considerations
* **Indexing Strategy**: B-tree indexes on `user_id` and `created_at` across all tracking tables.
