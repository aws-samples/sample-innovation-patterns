# web-client Makefile
# Convenience targets for development and CI/CD workflows
#
# Usage:
#   make lint        — Format + lint with auto-fix (local development)
#   make lint-cicd   — Check format + lint without fixing (CI gate, fails on violations)

# ──────────────────────────────────────────────
# Color codes for terminal output
# ──────────────────────────────────────────────
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m  # No Color

# ──────────────────────────────────────────────
# Local Development
# ──────────────────────────────────────────────

## lint: Format all source files with Prettier, then run ESLint with auto-fix.
##       Use this during local development to keep code clean.
lint:
	@echo "Formatting with Prettier..."
	npm run format
	@echo "Linting with ESLint (auto-fix)..."
	npm run lint
	@echo -e "$(GREEN)Format + lint complete.$(NC)"

# ──────────────────────────────────────────────
# CI/CD
# ──────────────────────────────────────────────

## lint-cicd: Check formatting and lint without modifying files.
##            Exits non-zero if any violations are found.
##            Use this in CI pipelines as a quality gate.
lint-cicd:
	npm run lint:cicd:junit
