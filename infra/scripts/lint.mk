# Lint & format automation
# Usage: make -f infra/scripts/lint.mk <target>
#   (the root Makefile exposes `make lint` as a convenience wrapper)
#
# Targets must be invoked from the repository root so the `cd <project>`
# recipes resolve correctly.
#
# Fix everything:      make -f infra/scripts/lint.mk lint
# Check only (no fix): make -f infra/scripts/lint.mk lint-check   (CI-style; fails on issues)
# Per project:         lint-app-lib | lint-web-client | lint-infra (+ lint-check-* variants)

.PHONY: lint lint-app-lib lint-web-client lint-infra \
        lint-check lint-check-app-lib lint-check-web-client lint-check-infra

# ---------------------------------------------------------------------------
# Auto-fix everything, then run the checks that can't auto-fix
# ---------------------------------------------------------------------------

# One command to fix all lint/format issues across the repo before commit/push.
lint: lint-app-lib lint-web-client lint-infra
	@echo "✓ lint complete — all projects formatted and auto-fixed"

# Python backend: ruff auto-fix + format + import-boundary check.
lint-app-lib:
	@echo "→ app-lib (ruff)"
	cd app-lib && uv run ruff check --fix && uv run ruff format && uv run python ../scripts/lint/check_import_boundaries.py src/app_lib

# React frontend: prettier --write + eslint --fix (the package.json "lint" script).
lint-web-client:
	@echo "→ web-client (prettier + eslint)"
	cd web-client && npm run lint

# Infrastructure: terraform fmt rewrites all *.tf in place. CloudFormation YAML
# has no auto-formatter; it is validated (not reformatted) by lint-check-infra.
lint-infra:
	@echo "→ infra (terraform fmt)"
	cd infra/tf && terraform fmt -recursive

# ---------------------------------------------------------------------------
# Check-only variants — no writes; exit non-zero on issues (mirror CI)
# ---------------------------------------------------------------------------

lint-check: lint-check-app-lib lint-check-web-client lint-check-infra
	@echo "✓ lint-check complete — no issues"

lint-check-app-lib:
	@echo "→ app-lib (ruff check)"
	cd app-lib && uv run ruff check && uv run ruff format --check && uv run python ../scripts/lint/check_import_boundaries.py src/app_lib

lint-check-web-client:
	@echo "→ web-client (prettier + eslint, check only)"
	cd web-client && npm run lint:cicd

lint-check-infra:
	@echo "→ infra (terraform fmt --check)"
	cd infra/tf && terraform fmt -recursive -check
