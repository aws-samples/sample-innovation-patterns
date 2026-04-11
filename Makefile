# Local Development
# Start the full stack: make dev
# Backend only:        make dev-backend
# Frontend only:       make dev-frontend

.PHONY: dev dev-backend dev-frontend

# Start backend (port 8000) and frontend (port 8080) concurrently.
# Ctrl+C stops both processes.
dev:
	@echo "Starting backend (:8000) and frontend (:8080)..."
	@echo "Press Ctrl+C to stop both services."
	@trap 'kill 0' INT TERM; \
	  $(MAKE) dev-backend & \
	  $(MAKE) dev-frontend & \
	  wait

# FastAPI backend with auto-reload (uv run finds the .venv automatically)
dev-backend:
	cd app-lib && uv run uvicorn app_lib.common.app:app --reload --port 8000

# Vite dev server (proxies /api to backend)
dev-frontend:
	cd web-client && npm run dev
