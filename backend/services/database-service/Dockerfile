FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Install system dependencies and security patches
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files (from monorepo root)
COPY backend/pyproject.toml /app/pyproject.toml
COPY backend/poetry.lock /app/poetry.lock

# Install Python dependencies
RUN poetry config virtualenvs.create false && poetry install --only main --no-root

# Copy shared libraries
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/shared /app/backend/shared

# Copy Kafka event schemas
COPY schemas /app/schemas

# Copy database service app
COPY backend/services/database-service/app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
