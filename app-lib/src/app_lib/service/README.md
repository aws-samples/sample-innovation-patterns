# Service Layer

Business logic and data access services.

## Structure

- `data/` — Data services wrapping PynamoDB models (see `data/common/README.md`)
- `inference/` — AI/ML inference services (see `inference/README.md`)
- `queue/` — Queue services (SQS)

## Adding a New Service

1. Create directory: `service/{category}/{name}/`
2. Implement service class
3. Add `__init__.py` with exports
4. See existing services for patterns
