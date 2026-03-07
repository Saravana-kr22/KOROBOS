#!/bin/bash
set -e

echo "Setting up CortexOS development environment..."

# 1. Install Backend Dependencies
echo "Installing backend dependencies..."
cd backend
poetry install
cd ..

# 2. Install Frontend Dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# 3. Setup Pre-commit Hooks
echo "Setting up pre-commit hooks..."
# Ensure pre-commit is installed globally or in venv
pip install pre-commit
pre-commit install

echo "Setup complete! Run 'make run' to start infrastructure, then 'make dev' to start services."
