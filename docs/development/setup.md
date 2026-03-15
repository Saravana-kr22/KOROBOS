# KOROBOS Developer Setup Guide

Welcome to the KOROBOS engineering team! Follow these steps to get your local environment running.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git
- Make
- Poetry (`pip install poetry`)

## 1. Clone Repository

```bash
git clone <repository-url>
cd KOROBOS
```

## 2. Install Dependencies

Run the initial setup script to install frontend/backend dependencies and pre-commit hooks.

```bash
make setup
```

## 3. Start Infrastructure

Start the development infrastructure (PostgreSQL, Redis, Kafka, Meilisearch, MinIO).

```bash
make run
```

Verify all containers are up:

```bash
docker compose ps
```

## 4. Environment Variables

Copy the development environment templates into local configurations:

```bash
cp configs/dev.env .env
```

(Adjust values as needed for your local setup).

## 5. Run Services

Start the frontend and backend servers concurrently:

```bash
make dev
```

Alternatively, you can run them manually:

- **Backend:** `cd backend && poetry run uvicorn services.auth-service.app.main:app --reload`
- **Frontend:** `cd frontend && npm run dev`

You are now ready to develop!
