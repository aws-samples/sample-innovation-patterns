# App-lib Makefile
# Convenience targets for development workflows

# Define color codes for terminal output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m  # No Color

# Install all dependencies using uv (preferred for local dev)
sync:
	uv sync --all-extras

# Register Jupyter kernel for notebooks
ipykernel:
	uv run python -m ipykernel install --user --env VIRTUAL_ENV $(pwd)/.venv --name app-lib --display-name "app-lib (uv)"

# Install package with all optional dependencies (pip-based, used in CI/Docker)
install:
	pip install -e ".[all]"

install_cicd:
	pip install -e ".[all]"

# Run linting checks and automatically fix issues
lint:
	ruff check --fix
	ruff format

# CI/CD version of lint that only checks but doesn't modify files
# Used in CI pipelines to verify code quality without making changes
lint-cicd:
	ruff check --output-format=junit -o lint-ruff.xml || true
	ruff format --check
	@ruff check --quiet

# Custom lint: Check PynamoDB attributes have null=True
lint-pynamodb:
	python ../scripts/lint/check_pynamodb_null.py

# Strict lint check for CI/CD (currently disabled, see lint-cicd_x for reference)
lint-cicd_x:
	@echo "Running code quality checks..."
	@if ! ruff check; then \
		echo -e "$(RED)ERROR: Ruff linting failed!$(NC)"; \
		echo -e "$(YELLOW)Please run 'make ruff-lint' locally to fix these issues.$(NC)"; \
		exit 1; \
	fi
	@if ! ruff format --check; then \
		echo -e "$(RED)ERROR: Code formatting check failed!$(NC)"; \
		echo -e "$(YELLOW)Please run 'make format' locally to fix these issues.$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)All code quality checks passed!$(NC)"

# Run unit tests (delegates to tests/Makefile)
test:
	$(MAKE) test -C ./tests

test_cicd:
	pytest --cov=app_lib --cov-report=term --cov-report=xml --junitxml=junit.xml

# Run integration tests
integration:
	$(MAKE) integration -C ./tests

integration_cicd:
	pytest tests/integration/ --cov=app_lib --cov-report=term --cov-report=xml --junitxml=junit.xml

########################################
# DEV Targets
########################################

# Local dev server
run:
	cd src/app_lib/common && $(MAKE) dev

########################################
# End DEV Targets
########################################
