# features/

Business features. Each feature is a self-contained directory under `features/`.

## Feature Layout

```
features/{name}/
├── __init__.py       # Exports router
├── model/            # PynamoDB models
├── service/          # Business logic, data access
├── routes/           # FastAPI routers + Pydantic DTOs
└── util/             # Feature-specific utilities
```

## Firewall Rule

- Features may import from `common/*`
- Features may import from their own subdirectories
- Features MUST NOT import from other features
- To add: create directory, add 2 lines in `common/app.py`
- To remove: delete directory, remove 2 lines from `common/app.py`, delete `tests/features/{name}/`
