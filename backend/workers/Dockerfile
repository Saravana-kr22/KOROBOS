# CortexOS — Second Brain Operating System
#
# Copyright (c) 2026 Saravana Perumal K
#
# Licensed under the GNU Affero General Public License v3.

FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install poetry

COPY backend/pyproject.toml /app/pyproject.toml
COPY backend/poetry.lock /app/poetry.lock
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root

COPY backend/__init__.py /app/backend/__init__.py
COPY backend/shared /app/backend/shared
COPY backend/workers /app/backend/workers
COPY schemas /app/schemas
COPY backend/services/analytics-service/app /app/backend/services/analytics-service/app
COPY backend/services/notification-service/app /app/backend/services/notification-service/app
COPY backend/services/ai-service/app /app/backend/services/ai-service/app

CMD ["python", "-m", "backend.workers.analytics_worker"]
