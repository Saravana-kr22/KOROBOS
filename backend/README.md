# CortexOS Backend

Microservices monorepo.

## Structure
- `gateway/`: API Gateway
- `services/`: Microservices (auth, notes, habit, etc.)
- `shared/`: Shared libraries for python (database, messaging, etc.)
- `workers/`: Background workers

## Commands
Install deps: `poetry install`
Format: `poetry run ruff format .`
Lint: `poetry run ruff check .`
Type check: `poetry run mypy .`
Test: `poetry run pytest`
