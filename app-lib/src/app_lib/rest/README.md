# REST API

FastAPI REST API with versioned feature-based routing.

## Structure

    rest/
    ├── app.py              # FastAPI app — mounts routers, CORS, auth middleware
    ├── auth.py             # JWT authentication middleware (OIDC-compatible)
    └── v1/
        ├── passengers/     # Titanic CRUD (example — delete to remove)
        │   ├── routes.py   # APIRouter(prefix="/api/v1")
        │   └── dto.py      # Pydantic request/response DTOs
        └── sse/            # SSE streaming (echo, playground)
            ├── routes.py
            └── playground_dto.py

Job routes live in `patterns/sqs/` — see that pattern's README for details.

## Adding a Feature

1. Create `v1/yourfeature/` with `__init__.py`, `routes.py`, `dto.py`
2. Define an `APIRouter` with appropriate prefix and tags
3. Mount in `app.py`: `app.include_router(your_router)`

## Naming Conventions

- `routes.py` — FastAPI route definitions (one per feature directory)
- `dto.py` — Pydantic request/response DTOs (not data models)

## Running Locally

    cd app-lib && pip install -e ".[rest]"
    cd src/app_lib/rest && make dev

API at http://localhost:8000. Docs at http://localhost:8000/docs.
