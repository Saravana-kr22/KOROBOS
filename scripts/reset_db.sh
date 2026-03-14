#!/bin/bash
set -e

echo "Resetting KOROBOS database..."

# Assumes postgres is running locally via docker
docker exec -i korobos-postgres-1 psql -U korobos -d korobos -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "Database reset complete."
