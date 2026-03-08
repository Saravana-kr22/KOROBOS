FROM python:3.11-slim

WORKDIR /app

# Install basic system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY gateway/api-gateway/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source code
COPY gateway/api-gateway/app /app/app

# Expose typical gateway port
EXPOSE 8000

# Default command for FastAPI/Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
