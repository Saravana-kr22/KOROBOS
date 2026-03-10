.PHONY: \
	setup install install-backend install-frontend \
	dev run stop \
	test test-backend test-backend-integration test-frontend \
	lint lint-backend lint-frontend \
	format format-backend check-format-backend \
	build build-frontend \
	ci cd verify-deploy-branch update-helm-values sync-argocd \
	reset-db seed-data

BACKEND_DIR := backend
FRONTEND_DIR := frontend
CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null)
SHORT_SHA := $(shell git rev-parse --short HEAD 2>/dev/null)
GITHUB_REPOSITORY := $(shell git config --get remote.origin.url | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$$##' | tr '[:upper:]' '[:lower:]')
IMAGE_PREFIX ?= $(if $(GITHUB_REPOSITORY),ghcr.io/$(GITHUB_REPOSITORY),ghcr.io/saravana-kr22/cortexos)
HELM_VALUES_FILES := $(wildcard infrastructure/helm/charts/*/values.yaml)

setup:
	bash scripts/setup_dev.sh

install: install-backend install-frontend

install-backend:
	cd $(BACKEND_DIR) && poetry install --with dev

install-frontend:
	cd $(FRONTEND_DIR) && npm ci --legacy-peer-deps

dev:
	bash scripts/start_dev.sh

test: test-backend test-backend-integration test-frontend

test-backend:
	cd $(BACKEND_DIR) && poetry run pytest tests -q --ignore=tests/test_messaging_integration.py

test-backend-integration:
	cd $(BACKEND_DIR) && poetry run pytest tests/test_messaging_integration.py -q

test-frontend: build-frontend

lint: lint-backend lint-frontend

lint-backend:
	cd $(BACKEND_DIR) && poetry run ruff check .

lint-frontend:
	cd $(FRONTEND_DIR) && npm run lint

format: format-backend

format-backend:
	cd $(BACKEND_DIR) && poetry run ruff format .

check-format-backend:
	cd $(BACKEND_DIR) && poetry run ruff format --check .

build: build-frontend

build-frontend:
	cd $(FRONTEND_DIR) && npm run build

ci: lint-backend check-format-backend test-backend test-backend-integration lint-frontend build-frontend

cd: ci verify-deploy-branch update-helm-values
	@if [ "$(CURRENT_BRANCH)" = "develop" ]; then \
		echo "Helm values updated for develop with sha-$(SHORT_SHA). Commit and push to continue the GitOps flow and let the workflow trigger ArgoCD sync."; \
	elif [ "$(CURRENT_BRANCH)" = "main" ]; then \
		echo "Helm values updated for main with sha-$(SHORT_SHA). Commit and push to continue the staging and production workflow."; \
	fi

verify-deploy-branch:
	@if [ "$(CURRENT_BRANCH)" != "develop" ] && [ "$(CURRENT_BRANCH)" != "main" ]; then \
		echo "cd mirrors the GitHub deployment flow and only supports 'develop' or 'main'. Current branch: $(CURRENT_BRANCH)"; \
		exit 1; \
	fi
	@if [ -z "$(SHORT_SHA)" ]; then \
		echo "Unable to determine the current git SHA for deployment tagging."; \
		exit 1; \
	fi

update-helm-values:
	@for chart_path in $(HELM_VALUES_FILES); do \
		svc=$$(basename "$$(dirname "$$chart_path")"); \
		sed -i "s|tag: \".*\"|tag: \"sha-$(SHORT_SHA)\"|g" "$$chart_path"; \
		sed -i "s|repository: .*|repository: $(IMAGE_PREFIX)/$$svc|g" "$$chart_path"; \
	done

sync-argocd:
	@if [ "$(CURRENT_BRANCH)" = "develop" ] && [ -n "$(ARGOCD_SERVER)" ] && [ -n "$(ARGOCD_TOKEN)" ]; then \
		for chart_path in $(HELM_VALUES_FILES); do \
			svc=$$(basename "$$(dirname "$$chart_path")"); \
			curl -s -X POST "https://$(ARGOCD_SERVER)/api/v1/applications/$$svc/sync" \
				-H "Authorization: Bearer $(ARGOCD_TOKEN)" \
				-H "Content-Type: application/json" \
				-d '{}' || echo "ArgoCD sync for $$svc skipped"; \
		done; \
	elif [ "$(CURRENT_BRANCH)" = "develop" ]; then \
		echo "ARGOCD_SERVER or ARGOCD_TOKEN not set; skipping ArgoCD sync."; \
	elif [ "$(CURRENT_BRANCH)" = "main" ]; then \
		echo "Main branch matches the staging chart update flow. Production promotion remains workflow-managed."; \
	else \
		echo "No ArgoCD action configured for branch $(CURRENT_BRANCH)."; \
	fi

reset-db:
	bash scripts/reset_db.sh

seed-data:
	bash scripts/seed_data.sh

run:
	docker compose up -d

stop:
	bash scripts/stop_dev.sh
