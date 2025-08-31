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

deploy: ## Deploy info (Render is primary deployment target)
	@echo "Primary deployment: Render (auto-deploy enabled for main branch)"
	@echo "Render dashboard: https://dashboard.render.com"
	@echo "To deploy manually: git push origin main"
	@echo ""
	@echo "Fly.io deployment disabled by default. To re-enable:"
	@echo "  1. Remove 'if: false' from .github/workflows/release.yml"
	@echo "  2. Restore FLY_API_TOKEN secret in GitHub"
	@echo "  3. Run: flyctl deploy --app youtube-tracker"

# Fly.io commands disabled - using Render as primary deployment target
rollback: ## Rollback info (Render platform)
	@echo "For Render rollbacks:"
	@echo "  1. Go to Render dashboard"
	@echo "  2. Select service -> Deploys tab"
	@echo "  3. Click 'Redeploy' on previous successful deployment"
	@echo ""
	@echo "For git-based rollback:"
	@echo "  git revert <commit-hash> && git push origin main"

rollback-to: ## Rollback to specific version (git-based)
	@echo "Usage: git revert <commit-hash> && git push origin main"
	@echo "Find commit hash: git log --oneline"

list-releases: ## List available releases
	@echo "View releases at: https://github.com/ympnov22/youtube-disappeared-tracker/releases"
	@echo "View Render deploys at: https://dashboard.render.com"

status: ## Check deployment status
	@echo "Check Render status at: https://dashboard.render.com"
	@echo "Health check: curl -f https://youtube-disappeared-tracker.onrender.com/health"

logs: ## View application logs
	@echo "View logs at Render dashboard: https://dashboard.render.com"
	@echo "Or use: curl https://youtube-disappeared-tracker.onrender.com/health"

health: ## Check application health (Render)
	@echo "Testing Render deployment health..."
	curl -f https://youtube-disappeared-tracker.onrender.com/health || echo "Health check failed - check Render dashboard"
