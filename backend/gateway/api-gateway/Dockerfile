# KOROBOS — Second Brain Operating System
#
# Copyright (c) 2026 Saravana Perumal K
#
# Licensed under the GNU Affero General Public License v3.

FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Install basic system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY backend/gateway/api-gateway/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source code and shared backend libraries
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/shared /app/backend/shared
COPY backend/gateway/api-gateway/app /app/app

# Expose typical gateway port
EXPOSE 8000

# Default command for FastAPI/Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
