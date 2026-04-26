---
title: Formatting and Linting
sidebar_position: 6
---

# Formatting and Linting

The app-lib codebase uses [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting. Ruff replaces Black, Flake8, isort, and pydocstyle with a single tool configured via `app-lib/ruff.toml`. All formatting and lint rules auto-fix on `make lint`.

## Overview

Ruff runs two passes on every `make lint` invocation:

1. **`ruff check --fix`** — Lint pass. Detects code quality issues and auto-fixes where possible (unused imports, import sorting, style violations).
2. **`ruff format`** — Format pass. Applies Black-compatible formatting (line length, quote style, indentation).

Both commands read their configuration from `app-lib/ruff.toml`. Ruff is declared as a dev dependency in `pyproject.toml` (`ruff>=0.14.10,<1.0.0`) and installed via `uv sync --all-extras` or `pip install -e ".[all]"`.

## Key Concepts

### Rule Selection

The `ruff.toml` `[lint]` section selects which rule families are active:

| Code | Family | What It Catches |
|------|--------|----------------|
| `E4`, `E7`, `E9` | pycodestyle (subset) | Indentation, statement, and runtime errors |
| `F` | Pyflakes | Undefined names, unused imports, redefined variables |
| `D` | pydocstyle | Missing or malformed docstrings (Google convention) |
| `I` | isort | Import ordering (via `extend-select`) |

All enabled rules are auto-fixable (`fixable = ["ALL"]`). Rules not in this list (e.g., McCabe complexity `C901`, pycodestyle warnings `W`) are not enforced.

### Per-File Ignores

Certain directories have relaxed rules to avoid noise:

| Path Pattern | Ignored Rules | Reason |
|-------------|---------------|--------|
| `**/notebooks/*` | `F401`, `D` | Notebooks commonly have unused imports and lack docstrings |
| `src/**/*.py` | `E402` | Module-level imports may follow path manipulation |
| `tests/**/*.py` | `D` | Tests do not require docstrings |
| `**/__init__.py` | `D104` | Package-level `__init__.py` files do not require module docstrings |

### Formatting Rules

The `[format]` section follows Black conventions:

- **Line length:** 88 characters
- **Indent:** 4 spaces
- **Quotes:** Double quotes
- **Trailing commas:** Preserved (magic trailing comma respected)
- **Line endings:** Auto-detected

### Docstring Convention

Ruff enforces Google-style docstrings via `[lint.pydocstyle] convention = "google"`. This applies to all `.py` files under `src/` (tests and notebooks are exempt). Docstrings auto-render to the MkDocs API reference site via mkdocstrings.

## Usage

### Local Development

From the `app-lib/` directory:

```bash
# Fix lint issues and format all files
make lint

# Run the local dev server (uvicorn on port 8000)
make run
```

`make lint` runs both `ruff check --fix` and `ruff format` in sequence. It modifies files in place — review changes with `git diff` before committing.

### CI/CD

The CI pipeline uses a separate target that checks without modifying files:

```bash
# Check-only mode (no file modifications)
make lint-cicd
```

This target:
1. Runs `ruff check --output-format=junit -o lint-ruff.xml` to produce a JUnit report (non-blocking — `|| true`).
2. Runs `ruff format --check` to verify formatting without applying changes.
3. Runs `ruff check --quiet` as the actual gate — exits non-zero on violations.

### Editor Integration

Ruff integrates with VS Code and JetBrains via official extensions. The extension reads `ruff.toml` automatically when the workspace root contains it. To enable format-on-save and organize-imports-on-save, add to `.vscode/settings.json`:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

## Extending / Maintaining

### Key Files

| File | Purpose |
|------|---------|
| `app-lib/ruff.toml` | All lint and format configuration |
| `app-lib/Makefile` | `lint` and `lint-cicd` targets |
| `app-lib/pyproject.toml` | Ruff version pin (`ruff>=0.14.10,<1.0.0`) |

### Adding a New Lint Rule

To enable a new rule family (e.g., `UP` for pyupgrade):

1. Add the rule code to `select` or `extend-select` in `ruff.toml`.
2. Run `make lint` to auto-fix existing violations.
3. Review changes and commit.

To suppress a rule for a specific directory, add an entry to `[lint.per-file-ignores]`.

### Relationship to CI Pipeline

The `lint-cicd` target produces `lint-ruff.xml` (JUnit format) for CI reporting. The format check (`ruff format --check`) and the quiet lint check (`ruff check --quiet`) are the actual pass/fail gates. If `make lint-cicd` fails in CI, run `make lint` locally to auto-fix, then commit the changes.

## References

- `app-lib/ruff.toml` — lint and format configuration
- `app-lib/Makefile` — Make targets for lint, format, and CI
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [Ruff rule reference](https://docs.astral.sh/ruff/rules/)
