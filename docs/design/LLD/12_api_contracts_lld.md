# KOROBOS – Enterprise LLD Template

Document Name: API Contracts Low Level Design
Project: KOROBOS – Second Brain Operating System
Version: 1.0
Author: Saravana Perumal K
Date: 2026-03-07
Status: Draft

## 1. Overview

### 1.1 Purpose

Standardizes communication protocols between the Frontend and Microservices.

## 2. Standards

- **Protocol**: RESTful JSON.
- **Authentication**: Bearer JWT in Header.
- **Versioning**: Prefix `/api/v1/`.

## 3. Common API Patterns

### 3.1 Error Response

```json
{
  "error_code": "STRING_ID",
  "message": "Human readable error"
}
```

## **4\. Rate Limiting**

- **Config**: 100 requests/min per user; 1000 requests/min per IP.
