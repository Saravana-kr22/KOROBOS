# KOROBOS — Second Brain Operating System
#
# Copyright (c) 2026 Saravana Perumal K
#
# Licensed under the GNU Affero General Public License v3.
#
# Dashboard Service Docker image.

FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

# Copy dependencies
COPY backend/pyproject.toml /app/pyproject.toml
COPY backend/poetry.lock /app/poetry.lock
RUN poetry config virtualenvs.create false && poetry install --only main --no-root

# Install Prometheus metrics library
RUN pip install --no-cache-dir prometheus-client==0.20.0

# Copy shared + service code
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/shared /app/backend/shared
COPY backend/services/dashboard-service/app /app/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
