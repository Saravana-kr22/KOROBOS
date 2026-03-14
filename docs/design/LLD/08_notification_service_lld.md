# KOROBOS – Enterprise LLD Template

Document Name: Notification Service Low Level Design
Project: KOROBOS – Second Brain Operating System
Version: 1.0
Author: Saravana Perumal K
Date: 2026-03-07
Status: Draft

## 1. Overview

### 1.1 Purpose

The Notification Service handles push and email alerts for reminders and system updates.

### 1.2 Scope

**In Scope**

- Habit, workout, and learning reminders.
- Push notification delivery via mobile/browser.
- Email notification delivery.

### 1.3 Dependencies

| Dependency    | Purpose                            |
| :------------ | :--------------------------------- |
| EventBus      | Consuming trigger events.          |
| Email Service | Third-party SMTP/API for delivery. |

## 2. Architecture

### 2.1 Component Overview

Notification API → Scheduler → Delivery Manager → Provider Gateways.

## 3. Event Architecture

### 3.1 Notification Event Flow

1. `habit_completed` event arrives via EventBus.
2. Scheduler calculates the next reminder time.
3. Delivery Manager pushes to specific user channel.

## 4. Failure Handling

- **Retry**: Failed delivery attempts retried via exponential backoff queue.
