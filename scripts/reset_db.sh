#!/bin/bash
set -e

echo "Resetting CortexOS database..."

# Assumes postgres is running locally via docker
docker exec -i cortexos-postgres-1 psql -U cortexos -d cortexos -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "Database reset complete."
