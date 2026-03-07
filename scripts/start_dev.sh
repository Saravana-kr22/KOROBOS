#!/bin/bash
set -e

echo "Starting CortexOS development servers..."

# Start Backend (Auth Service as example)
# In a real setup, we might use a process manager like Overmind/Foreman or Docker Compose for services.
echo "Starting Auth Service on port 8000..."
cd backend
poetry run uvicorn services.auth-service.app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "Starting Next.js frontend on port 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Servers running. Press Ctrl+C to stop."

# Wait for termination signal
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM
wait
