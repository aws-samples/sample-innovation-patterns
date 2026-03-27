# Titanic Passenger Data Service

DynamoDB-backed implementation of `AbstractDataService` for the Titanic passenger dataset.

## Design Decisions

- **`T` is the PynamoDB model directly.** `TitanicPassengerTable` is used as the entity type rather than introducing a separate domain model. This keeps the implementation simple. If a decoupled domain layer is needed later, only this class changes — consumers are unaffected.
- **Filtering is in-memory.** `query()` scans the table and filters in Python. This works for the ~1300 record dataset. A larger dataset would require DynamoDB GSIs or a different backing store.
- **`save` is upsert.** PynamoDB's `save()` creates or overwrites. There is no separate create vs. update distinction.

## Consumers

- `titanic_mcp_server.py` — MCP tools for agent interactions
- `load_dynamodb_util.py` — CSV data loader
- `api_lambda_handler.py` — FastAPI REST interface (planned)
