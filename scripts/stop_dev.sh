#!/bin/bash
set -e

echo "Stopping KOROBOS development environment..."

# Stop all containers defined in docker-compose.yml
docker compose down

echo ""
echo "=================================================="
echo "🛑 All KOROBOS services and infrastructure stopped."
echo "=================================================="
