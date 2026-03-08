# CortexOS — Copyright (c) 2026 Saravana Perumal K — AGPL v3

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install poetry

# Copy pyproject and install dependencies
COPY pyproject.toml /app/
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root

# Copy shared libraries and service source code
COPY shared /app/shared
COPY services/analytics-service/app /app/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
