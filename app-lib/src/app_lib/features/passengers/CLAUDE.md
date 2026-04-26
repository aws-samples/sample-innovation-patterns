# features/passengers/

Titanic passenger CRUD demo feature. Reference implementation for the feature-centric pattern — copy this directory to bootstrap a new feature.

- Routes at `/api/v1/passengers` — CRUD via `TitanicPassengerDataService` (DynamoDB-backed).
- Ticket IDs can contain slashes (e.g., `SC/AH 29037`) — routes use `{ticket:path}` to match across path separators.
- `passenger_dto.py:TitanicPassengerResponse.from_model()` converts PynamoDB `Decimal` to Python `int`/`float` — copy this pattern for any PynamoDB model with numeric attributes.
- `load_dynamodb_util.py` is a standalone CLI tool: `python -m app_lib.features.passengers.util.load_dynamodb_util`.
- DynamoDB table name: `{APP_NAMESPACE}_{APP_ENV}_passengers` (via `PynamodbUtil`).
- Remove this feature: delete this directory, remove 2 lines from `common/app.py`, delete `tests/features/passengers/`.

See `../CLAUDE.md` for the feature contract and extension recipe.

## File Map

| File | Role | Key Exports |
|------|------|-------------|
| `model/passenger_table.py` | PynamoDB model | `TitanicPassengerTable` |
| `service/passenger_data_service.py` | CRUD service | `TitanicPassengerDataService` (extends `AbstractDataService[TitanicPassengerTable]`) |
| `routes/passenger_routes.py` | FastAPI router | `router` — mounted by `common/app.py` |
| `routes/passenger_dto.py` | Pydantic DTOs | `TitanicPassengerCreate`, `TitanicPassengerResponse` |
| `util/load_dynamodb_util.py` | CSV loader CLI | `LoadDynamoDbUtil` |
