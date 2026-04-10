# app-lib/

Reusable Python library providing feature-centric REST API patterns for AWS applications. FastAPI + PynamoDB + Lambda Web Adapter.

- Python 3.12, managed with `uv`. Install: `pip install -e ".[all]"`.
- Lint/format: `make lint` (ruff, line-length 88, Google-style docstrings).
- Tests: `make test` (pytest). Tests mirror source: `tests/features/` and `tests/common/`.
- Feature-centric layout: each feature is self-contained under `features/{name}/`. Features import from `common/`, never from each other.
- **To add a feature**: see `src/app_lib/features/CLAUDE.md` for the step-by-step recipe.
- `PathUtil.lib_root()` resolves to `src/app_lib/` — it uses `__file__` parent traversal from `common/util/path_util.py` (3 levels up).
- `PynamodbUtil.env_table_name(base)` prefixes table names with `{APP_NAMESPACE}_{APP_ENV}_` — all PynamoDB models must use this.
- Lambda handlers in `common/lambda/` are COPYed to container root by `infra/containers/rest-lambda/Dockerfile`.

See README.md for full conventions. See `src/app_lib/features/CLAUDE.md` for feature conventions. See `src/app_lib/common/CLAUDE.md` for shared infrastructure conventions.

## Code Organization

```
src/app_lib/
├── common/                          # Shared infrastructure
│   ├── app.py                       # FastAPI app, middleware, feature router registration
│   ├── auth.py                      # JWT auth middleware (OIDC-compliant)
│   ├── Makefile                     # Local dev: uvicorn on port 8000
│   ├── data/
│   │   └── abstract_data_service.py # Generic CRUD interface — AbstractDataService[T]
│   ├── lambda/                      # Lambda entry points (copied to container root)
│   │   ├── api_lambda_handler.py    # REST API handler (imports app from common/app.py)
│   │   ├── lambda_handler.py        # Generic event handler template
│   │   └── s3_handler.py            # S3 file processor (SQS → S3 events)
│   └── util/
│       ├── path_util.py             # PathUtil — lib_root(), project_root(), lib_assets()
│       ├── pynamodb_util.py         # PynamodbUtil — env_table_name() for DynamoDB
│       ├── observability.py         # Structured logging, CloudWatch metrics, Bedrock usage
│       └── jinja_util.py            # Jinja2 template rendering
│
├── features/                        # Business features (self-contained)
│   └── passengers/                  # Demo feature — Titanic passenger CRUD
│       ├── model/passenger_table.py           # PynamoDB model
│       ├── service/passenger_data_service.py  # AbstractDataService[T] implementation
│       ├── routes/passenger_routes.py         # FastAPI router (/api/v1/passengers)
│       ├── routes/passenger_dto.py            # Pydantic request/response DTOs
│       └── util/load_dynamodb_util.py         # CSV → DynamoDB loader
│
└── assets/                          # Static assets and datasets
    └── datasets/titanic/            # Titanic CSV data

tests/
├── features/passengers/             # Passenger feature tests
├── common/util/                     # Shared utility tests
├── conftest.py                      # Shared fixtures
└── test_basic.py                    # Package-level smoke test
```

## Adding a New Feature (Quick Reference)

1. Create `features/{name}/` with `__init__.py`, `model/`, `service/`, `routes/`, `util/` (as needed)
2. Model: PynamoDB model using `PynamodbUtil.env_table_name("your_table")`
3. Service: extend `AbstractDataService[YourModel]` from `common.data`
4. Routes: FastAPI `APIRouter(prefix="/api/v1", tags=["your_feature"])`
5. Register in `common/app.py`: import router + `app.include_router(your_router)`
6. Add tests in `tests/features/{name}/`
7. If DynamoDB table needed: enable via feature flag in tier stack (e.g., `EnablePassengersTable=true` on backend, `EnableJobsTable=true` on queue)

## Coding Standards

### Docstrings
Google-style docstrings for all modules, classes, and functions. Ruff enforces via pydocstyle rules (`D` prefix). Docstrings auto-render to MKDocs via mkdocstrings.

### Ruff Configuration
See [ruff.toml](./ruff.toml): line-length 88, Python 3.9+ target, Pyflakes (F), pycodestyle (E4/E7/E9), isort (I), pydocstyle (D, Google convention), double quotes.

## Environment Variables

| Variable | Default | Used By |
|----------|---------|---------|
| `APP_NAMESPACE` | `""` | `PynamodbUtil` — DynamoDB table name prefix |
| `APP_ENV` | `"dev"` | `PynamodbUtil` — environment segment in table names |
| `API_STAGE_PREFIX` | `""` | `common/app.py` — FastAPI `root_path` for API Gateway |
| `CORS_ALLOWED_ORIGINS` | `"*"` | `common/app.py` — comma-separated origins |
| `AUTH_ENABLED` | `"false"` | `common/auth.py` — enable JWT validation |
| `OIDC_ISSUER` / `AUTH_ISSUER` | `""` | `common/auth.py` — OIDC issuer URL |
| `OIDC_CLIENT_ID` / `AUTH_AUDIENCE` | `""` | `common/auth.py` — expected audience |
| `APP_METRIC_NAMESPACE` | `"{namespace}/{env}"` | `observability.py` — CloudWatch metric namespace |
| `APP_VERSION` | `None` | `common/app.py` — version endpoint |
| `BUILD_VERSION` | `"dev"` | `common/app.py` — build identifier |

## Tests

- Tests in [tests/](./tests/) mirror `src/app_lib/` structure
- Run: `make test` or `pytest`
- See [tests/CLAUDE.md](./tests/CLAUDE.md) for test conventions
