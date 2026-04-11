---
title: Unit Testing
sidebar_position: 5
---

# Unit Testing

The `app-lib/` test suite uses pytest with `unittest.mock` for external dependencies. Tests mirror the source directory structure and run against mocked AWS services — no live infrastructure required.

## Overview

Tests live in `app-lib/tests/` and mirror the source layout under `src/app_lib/`:

```
tests/
├── conftest.py                 # Shared fixtures
├── test_basic.py               # Package-level smoke test
├── common/
│   └── util/
│       ├── test_pynamodb_util.py
│       ├── test_path_util.py
│       └── test_observability.py
├── features/
│   ├── passengers/
│   │   ├── test_passenger_table.py
│   │   ├── test_passenger_data_service.py
│   │   └── test_load_dynamodb_util.py
│   ├── jobs/
│   │   ├── test_job_table.py
│   │   ├── test_job_data_service.py
│   │   └── test_job_routes.py
│   └── inference/
│       └── test_inference_sse_routes.py
```

Each feature's tests correspond one-to-one with its source modules: model tests, service tests, and route tests.

## Key Concepts

### Configuration

`pytest.ini` defines the test discovery rules:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers
```

All test files must be named `test_*.py`, all test classes `Test*`, and all test functions `test_*`. The `--strict-markers` flag rejects any undeclared marker.

### Mocking External Dependencies

Tests mock AWS services rather than calling them. The two primary patterns are `@patch.object` for PynamoDB model methods and `@patch` for module-level dependencies.

**PynamoDB model methods** — mock `get`, `save`, `scan`, `count`, and `delete` on the model class directly:

```python
from unittest.mock import MagicMock, patch

@patch.object(TitanicPassengerTable, "get")
def test_get_success(mock_get, repository, mock_passenger):
    mock_get.return_value = mock_passenger
    result = repository.get("24160")
    assert result == mock_passenger
    mock_get.assert_called_once_with("24160")
```

**Module-level services** — mock the service instance referenced by route modules:

```python
@patch("app_lib.features.jobs.routes.job_routes.job_service")
def test_get_job(mock_service, client, mock_job):
    mock_service.get.return_value = mock_job
    resp = client.get("/api/v1/jobs/abc-123")
    assert resp.status_code == 200
```

**boto3 clients** — mock the client factory function rather than boto3 itself:

```python
@patch(
    "app_lib.features.inference.routes.inference_sse_routes._get_bedrock_client"
)
def test_converse_stream(mock_get_client, client):
    mock_client = MagicMock()
    mock_client.converse_stream.return_value = {"stream": []}
    mock_get_client.return_value = mock_client
    # ...
```

### Fixtures

Shared fixtures go in `tests/conftest.py`. Feature-specific fixtures go in the test file that uses them.

**Mock entity fixtures** create `MagicMock` objects with `spec=` set to the PynamoDB model. This ensures that accessing non-existent attributes raises `AttributeError`:

```python
@pytest.fixture
def mock_passenger():
    passenger = MagicMock(spec=TitanicPassengerTable)
    passenger.id = "24160"
    passenger.name = "Allen, Miss. Elisabeth Walton"
    passenger.pclass = 1
    return passenger
```

**Test client fixtures** disable JWT auth and create a FastAPI `TestClient`:

```python
@pytest.fixture
def client():
    with patch.dict("os.environ", {"AUTH_ENABLED": "false"}):
        from app_lib.common.app import app
        return TestClient(app)
```

### Test Organization by Layer

Each feature has up to three test categories, corresponding to the feature's subdirectories:

| Layer | Tests | What to Verify |
|-------|-------|----------------|
| Model | `test_{name}_table.py` | Attribute assignment, nullable fields, table name prefix |
| Service | `test_{name}_data_service.py` | CRUD operations against mocked PynamoDB methods |
| Routes | `test_{name}_routes.py` | HTTP status codes, response shapes, service delegation |

Route tests exercise the full request path through FastAPI using `TestClient`, while model and service tests call Python methods directly.

### Environment Patching

Tests that depend on environment variables use `patch.dict("os.environ", ...)` to set values without affecting other tests:

```python
def test_custom_env(self):
    with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=True):
        assert PynamodbUtil.env_table_name("passengers") == "staging_passengers"
```

Pass `clear=True` when the test requires a clean environment with no inherited variables.

## Usage

### Running Tests

From the `app-lib/` directory:

```bash
# Run all tests
make test

# Run with coverage report
pytest --cov=app_lib --cov-report=term-missing

# Run a specific feature's tests
pytest tests/features/passengers/

# Run a single test file
pytest tests/features/jobs/test_job_routes.py

# Run a single test by name
pytest -k "test_get_not_found"
```

### Adding Tests for a New Feature

1. Create `tests/features/{name}/` with an `__init__.py` file.

2. Add a model test file (`test_{name}_table.py`). Verify attribute assignment and nullable fields:

   ```python
   def test_model_attributes():
       record = YourTable(id="123", name="Test")
       assert record.id == "123"

   def test_table_name():
       assert "your_table" in YourTable.Meta.table_name
   ```

3. Add a service test file (`test_{name}_data_service.py`). Mock the PynamoDB model and verify each CRUD operation:

   ```python
   @patch.object(YourTable, "get")
   def test_get_success(mock_get, service, mock_entity):
       mock_get.return_value = mock_entity
       result = service.get("123")
       assert result == mock_entity
   ```

4. Add a route test file (`test_{name}_routes.py`). Use `TestClient` with auth disabled and mock the service:

   ```python
   @patch("app_lib.features.{name}.routes.{name}_routes.data_service")
   def test_list(mock_service, client, mock_entity):
       mock_service.query.return_value = [mock_entity]
       resp = client.get("/api/v1/{name}s")
       assert resp.status_code == 200
   ```
