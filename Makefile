.PHONY: dev test lint format run reset-db seed-data setup

setup:
	bash scripts/setup_dev.sh

dev:
	bash scripts/start_dev.sh

test:
	cd backend && poetry run pytest
	cd frontend && npm run test

lint:
	cd backend && poetry run ruff check .
	cd backend && poetry run mypy .
	cd frontend && npm run lint

format:
	cd backend && poetry run ruff format .
	cd frontend && npm run format

reset-db:
	bash scripts/reset_db.sh

seed-data:
	bash scripts/seed_data.sh

run:
	docker compose up -d

stop:
	bash scripts/stop_dev.sh
