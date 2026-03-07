#!/bin/bash
set -e

echo "Stopping CortexOS development environment..."

# Stop all containers defined in docker-compose.yml
docker compose down

echo ""
echo "=================================================="
echo "🛑 All CortexOS services and infrastructure stopped."
echo "=================================================="
