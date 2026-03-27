# Test Organization Guide

## Structure
Tests mirror the source code structure in `src/app_lib/`:

```
tests/
├── model/
│   └── ddb/                    # DynamoDB model tests
├── service/
│   └── repositories/           # Repository service tests
└── conftest.py                 # Shared fixtures
```

## Running Tests

From `app-lib/` directory:
- All tests: `pytest`
- Verbose: `pytest -v`
- Specific file: `pytest tests/model/ddb/test_ddb_titanic_passenger_table.py`
- From tests directory: `make test` (see `tests/Makefile` for targets)

## Writing Tests

**Naming**: `test_<module_name>.py` for test files, `test_<function_name>` for test functions

**Fixtures**: Define in `conftest.py` for shared fixtures, or in test files for local use

**Mocking**: Use `unittest.mock` to mock external dependencies (DynamoDB, APIs, etc.)

**Structure**:
```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_function_behavior(sample_data):
    # Arrange
    # Act
    result = function(sample_data)
    # Assert
    assert result == expected
```

## Coverage
Run `pytest --cov=app_lib --cov-report=term-missing` to see coverage report
