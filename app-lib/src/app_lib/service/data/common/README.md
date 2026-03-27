# Abstract Data Service

`AbstractDataService[T]` defines a standard CRUD interface that decouples consumers from any specific persistence backend.

## Why This Exists

Agents, MCP tools, and API handlers should depend on a data access contract — not on DynamoDB, PynamoDB, or any other storage technology. This ABC enforces that contract so implementations can be swapped without changing consumer code.

## Adding a New Data Service

1. Create a directory under `service/data/{entity}/`
2. Implement a class that inherits `AbstractDataService[T]` where `T` is the entity type
3. Implement all 6 methods: `get`, `save`, `delete`, `list`, `query`, `count`

The `T` type parameter can be anything — a PynamoDB model, a Pydantic model, a dataclass, or a plain dict. The choice depends on the backing store and how much abstraction the project needs.

> **Note:** The `list` method name shadows Python's builtin `list`. Files that inherit from this ABC should include `from __future__ import annotations` to avoid `TypeError` at class definition time.
