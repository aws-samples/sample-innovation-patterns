# Local Development
# Start the full stack: make dev
# Backend only:        make dev-backend
# Frontend only:       make dev-frontend

.PHONY: dev dev-backend dev-frontend

# FastAPI backend with auto-reload (uv run finds the .venv automatically)
dev-backend:
	cd app-lib && uv run uvicorn app_lib.common.app:app --reload --port 8000

# Vite dev server (proxies /api to backend)
dev-frontend:
	cd web-client && npm run dev
