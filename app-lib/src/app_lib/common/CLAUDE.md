# common/

Shared infrastructure used by all features.

## What belongs here

| Directory | Contents |
|-----------|----------|
| `app.py` | FastAPI app, middleware, feature router registration |
| `auth.py` | JWT authentication middleware |
| `data/` | Abstract base classes (e.g., `AbstractDataService[T]`) |
| `util/` | Shared utilities (`PathUtil`, `PynamodbUtil`, `JinjaUtil`, `observability`) |
| `lambda/` | Lambda handler entry points (`api_lambda_handler`, `lambda_handler`, `s3_handler`) |
| `Makefile` | Local dev server target |

## Firewall Rule

- `common/` MUST NOT import from `features/` — **except** `app.py` and `lambda/` which register/serve features
- All shared abstractions and utilities live here
- Features import from `common/`, not the other way around

## Lambda Handlers

Lambda handlers in `common/lambda/` are copied to the container root by the Dockerfile.
The `CMD` in the Dockerfile references them by module name (e.g., `api_lambda_handler:app`).
