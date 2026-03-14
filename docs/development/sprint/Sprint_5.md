# KOROBOS — Sprint 5 Execution Plan

## Authentication & Identity Service

Version: 1.0
Owner: Saravana Perumal

---

# 1. Sprint Objective

Sprint 5 implements the **Authentication & Identity Service** for KOROBOS.

This service is responsible for:

- User registration
- User authentication
- Token generation
- Identity verification
- Session management
- Mobile authentication support (React Native Android)
- Role and permission management
- Security enforcement

The authentication system must support:

- Web application (React / Next.js)
- Mobile application (React Native Android)
- Future mobile (iOS)
- API integrations

The service must be **secure, scalable, and cloud-native**.

---

# 2. Identity Architecture Overview

Authentication architecture:

        Client Apps
        ↓
        API Gateway
        ↓
        Auth Service
        ↓
        Identity Database
        ↓
        Token Service

Client types:

- Web browser (React)
- Android mobile app (React Native)
- Internal microservices
- Future integrations

Authentication model:

**OAuth2 + JWT tokens**

---

# 3. Supported Authentication Flows

The system must support the following authentication flows:

### 1. Email + Password Login

Standard login for web and mobile.

### 2. Token Refresh Flow

Used when access token expires.

### 3. Mobile Persistent Login

React Native apps store refresh token securely.

### 4. Service-to-Service Authentication

Microservices authenticate using internal tokens.

### 5. Optional Social Login (Future)

Google / Apple sign-in.

---

# 4. Authentication Tokens

Two-token model:

### Access Token

- JWT token
- short lifetime
- used for API access

Expiration:

15 minutes

### Refresh Token

- long-lived token
- used to generate new access tokens

Expiration:

30 days

---

# 5. JWT Token Structure

Example payload:

```json
{
 "sub": "user_id",
 "email": "user@example.com",
 "roles": ["user"],
 "iat": timestamp,
 "exp": timestamp
}
```

JWT signed using:

        HS256 or RS256

---

# 6. Auth Service Architecture

Service responsibilities:

- user registration
- password hashing
- login verification
- token generation
- token validation
- session management
- account security

Technology stack:

- FastAPI
- PostgreSQL
- Redis
- JWT
- bcrypt

---

# 7. Auth Service Directory Structure

backend/services/auth-service/

    app/
        main.py
        api/
            auth_routes.py
        services/
            auth_service.py
            token_service.py
        repositories/
            user_repository.py
        models/
            user_model.py
            session_model.py
        schemas/
            auth_schema.py
        security/
            password_hashing.py
            jwt_handler.py
        config/
            settings.py

    Dockerfile
    requirements.txt

---

# 8. Database Schema

Table: users

| Column         | Type      |
| -------------- | --------- |
| id             | UUID      |
| email          | TEXT      |
| password_hash  | TEXT      |
| created_at     | TIMESTAMP |
| is_active      | BOOLEAN   |
| email_verified | BOOLEAN   |

---

Table: sessions

| Column        | Type      |
| ------------- | --------- |
| id            | UUID      |
| user_id       | UUID      |
| refresh_token | TEXT      |
| created_at    | TIMESTAMP |
| expires_at    | TIMESTAMP |
| device_info   | TEXT      |

---

# 9. Password Security

Passwords must be hashed.

Algorithm:

        bcrypt

Process:

        password → salt → bcrypt hash

Never store plaintext passwords.

---

# 10. Signup Flow

User signup process:

        User submits email + password
        ↓
        Auth Service validates input
        ↓
        Password hashed
        ↓
        User record created
        ↓
        JWT tokens generated
        ↓
        Response returned

---

# 11. Login Flow

Login process:

        User enters credentials
        ↓
        Auth Service verifies password
        ↓
        Session created
        ↓
        Access token generated
        ↓
        Refresh token generated
        ↓
        Response returned

---

# 12. Token Refresh Flow

When access token expires:

        Client sends refresh token
        ↓
        Auth Service validates token
        ↓
        New access token generated
        ↓
        Returned to client

---

# 13. Logout Flow

Logout process:

        Client sends logout request
        ↓
        Auth Service invalidates refresh token
        ↓
        Session removed from database

---

# 14. Mobile Authentication (React Native)

React Native mobile apps must store tokens securely.

Storage options:

    - Android Secure Storage
    - Encrypted storage libraries

Flow:

    Mobile login → store refresh token securely → refresh access tokens automatically.

---

# 15. API Endpoints

Auth APIs:

POST /auth/signup
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET /auth/me

---

Example Signup Request:

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

---

Example Login Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

---

# 16. Middleware Integration

API Gateway must validate access tokens.

Middleware responsibilities:

- decode JWT
- validate signature
- extract user identity

---

# 17. Account Security

Security protections:

- password hashing
- rate limiting login attempts
- brute-force protection
- account lockout

Example rule:

5 failed logins → temporary lock.

---

# 18. Email Verification (Optional)

Flow:

        User registers
        ↓
        Verification email sent
        ↓
        User clicks link
        ↓
        Account activated

---

# 19. Password Reset

Password reset flow:

        User requests reset
        ↓
        Reset token generated
        ↓
        Email sent
        ↓
        User sets new password

---

# 20. Device Tracking

Sessions track device metadata.

Stored fields:

    - device type
    - OS
    - IP address
    - login timestamp

---

# 21. Role Management

Basic roles:

    user
    admin

Stored in users table.

Used for API authorization.

---

# 22. Service-to-Service Authentication

Internal services use:

Service tokens

Gateway validates service identity.

---

# 23. Rate Limiting

Login attempts limited.

Example:

    10 requests per minute per IP.

---

# 24. Observability

Metrics tracked:

- login success rate
- login failure rate
- token refresh frequency

Monitoring via:

    Prometheus
    Grafana

---

# 25. Security Best Practices

Security rules:

- TLS encryption
- JWT expiration enforcement
- strong password rules
- secure token storage

---

# 26. Testing Strategy

Tests required:

- authentication unit tests
- API integration tests
- token validation tests
- security tests

Tools:

    pytest
    httpx

---

# 27. Sprint Validation Checklist

Before sprint completion verify:

✔ user signup working
✔ login flow working
✔ token generation working
✔ refresh token flow working
✔ logout working
✔ mobile login supported
✔ JWT validation working
✔ database sessions stored
✔ API gateway middleware working

---

# Final Sprint Outcome

After Sprint 5 completion KOROBOS will have a **fully operational Authentication & Identity Service**.

Capabilities:

- secure login system
- mobile authentication support
- JWT based identity verification
- scalable identity architecture

The platform now supports **secure multi-client access (web + Android)** and is ready for full user-facing functionality.
