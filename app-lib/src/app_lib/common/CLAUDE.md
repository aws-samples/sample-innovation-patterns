# common/

Shared infrastructure used by all features. FastAPI app, JWT auth, abstract data layer, utilities, and Lambda handlers.

- `common/` MUST NOT import from `features/` — **except** `app.py` (router registration) and `lambda/s3_handler.py` (feature service usage).
- `app.py` is the single integration point: features register here via `import router` + `app.include_router()`.
- `AbstractDataService[T]` in `data/` is the CRUD contract — all feature services extend it.
- `PathUtil.lib_root()` resolves via 3 `.parent` hops from `common/util/path_util.py` — if you move this file, fix the depth.
- `PynamodbUtil.env_table_name(base)` reads `APP_NAMESPACE` and `APP_ENV` — all PynamoDB models must use it.
- Lambda handlers in `lambda/` are COPYed to container root by the Dockerfile — they import by module name, not package path.

See README.md for contents table and integration details.

## Contents

| File/Directory | Purpose |
|----------------|---------|
| `app.py` | FastAPI app, CORS, JWT, ObservabilityMiddleware, feature router registration |
| `auth.py` | `JWTAuthMiddleware` — OIDC Bearer token validation, `PUBLIC_PATHS` whitelist |
| `Makefile` | `make dev` — uvicorn on port 8000 |
| `data/abstract_data_service.py` | `AbstractDataService[T]` — generic CRUD interface (get, save, delete, list, query, count) |
| `lambda/api_lambda_handler.py` | REST Lambda entry point — imports `app` for Lambda Web Adapter |
| `lambda/lambda_handler.py` | Generic event handler template (echo/info demo) |
| `lambda/s3_handler.py` | S3 file processor — receives SQS→S3 events, processes CSV |
| `util/path_util.py` | `PathUtil` — `lib_root()`, `project_root()`, `lib_assets()` |
| `util/pynamodb_util.py` | `PynamodbUtil` — `env_table_name()` for namespace-aware DynamoDB table names |
| `util/observability.py` | `log_exception()`, `publish_metric()`, `log_bedrock_usage()` — CloudWatch integration |
| `util/jinja_util.py` | `JinjaUtil.render()` — Jinja2 template rendering (currently unused) |
