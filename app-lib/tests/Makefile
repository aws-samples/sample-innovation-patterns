# Test Makefile
# Run unit tests with various options

.PHONY: test test-verbose test-coverage test-watch test-model test-service clean

# Run all tests
test:
	pytest

# Run tests with verbose output
test-verbose:
	pytest -v

# Run tests with coverage report
test-coverage:
	pytest --cov=app_lib --cov-report=term-missing

# Run tests in watch mode (requires pytest-watch)
test-watch:
	pytest-watch

# Run only model tests
test-model:
	pytest tests/model/

# Run only service tests
test-service:
	pytest tests/service/

# Run specific test file
# Usage: make test-file FILE=tests/model/ddb/test_ddb_titanic_passenger_table.py
test-file:
	pytest $(FILE)

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
