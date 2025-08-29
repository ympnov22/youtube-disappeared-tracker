.PHONY: help install test lint deploy rollback status

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	poetry install

test: ## Run tests
	poetry run pytest --cov=app --cov-report=term-missing --cov-fail-under=85

lint: ## Run linting
	poetry run black --check .
	poetry run isort --check-only .
	poetry run flake8 .
	poetry run mypy app

format: ## Format code
	poetry run black .
	poetry run isort .

deploy: ## Deploy to Fly.io
	flyctl deploy --app youtube-tracker

rollback: ## Rollback to previous version
	python scripts/rollback.py

rollback-to: ## Rollback to specific version (usage: make rollback-to VERSION=123)
	python scripts/rollback.py --version $(VERSION)

list-releases: ## List available releases
	python scripts/rollback.py --list-releases

status: ## Check deployment status
	flyctl status --app youtube-tracker

logs: ## View application logs
	flyctl logs --app youtube-tracker

health: ## Check application health
	curl -f https://youtube-tracker.fly.dev/healthz || echo "Health check failed"
