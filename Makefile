# Local Development
# Start the full stack: make dev
# Backend only:        make dev-backend
# Frontend only:       make dev-frontend
#
# Lint & format (run before commit/push):
# Everything:          make lint        (auto-fixes app-lib, web-client, infra)
# Check only (no fix): make lint-check  (CI-style; fails on issues)
# Per project:         make -f infra/scripts/lint.mk lint-app-lib | lint-web-client | lint-infra

.PHONY: dev dev-backend dev-frontend lint lint-check

# FastAPI backend with auto-reload (uv run finds the .venv automatically)
dev-backend:
	cd app-lib && uv run uvicorn app_lib.common.app:app --reload --port 8000

# Vite dev server (proxies /api to backend)
dev-frontend:
	cd web-client && npm run dev

# Lint & format — see infra/scripts/lint.mk for per-project targets.
# `make lint` auto-fixes app-lib, web-client, and infra; `make lint-check`
# is the CI-style read-only variant. Both delegate to lint.mk.
lint:
	@$(MAKE) -f infra/scripts/lint.mk lint

lint-check:
	@$(MAKE) -f infra/scripts/lint.mk lint-check
