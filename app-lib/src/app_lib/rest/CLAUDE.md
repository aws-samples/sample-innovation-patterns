# rest/

FastAPI REST layer with feature-based subdirectories under `v1/`.

**Conventions:**
- Each feature gets a directory: `v1/{feature}/routes.py` + `v1/{feature}/dto.py`
- DTOs are `*_dto.py` (not `*_models.py`) — distinguishes from PynamoDB models
- Mount routers in `app.py` with `app.include_router()`
