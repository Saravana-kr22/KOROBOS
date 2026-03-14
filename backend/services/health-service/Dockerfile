# KOROBOS — Second Brain Operating System
#
# Copyright (c) 2026 Saravana Perumal K
#
# Licensed under the GNU Affero General Public License v3.

FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install poetry

# Copy pyproject and install dependencies
COPY backend/pyproject.toml /app/pyproject.toml
COPY backend/poetry.lock /app/poetry.lock
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root

# Copy shared libraries and service source code
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/shared /app/backend/shared
COPY schemas /app/schemas
COPY backend/services/health-service/app /app/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
