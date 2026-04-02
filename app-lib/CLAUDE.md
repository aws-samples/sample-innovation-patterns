# Python Guidance for Agentic Coding Assistants

## Environment Management
- Python environment managed with `uv` (see `pyproject.toml` and `uv.lock`)
- Implementation is tool-agnostic - developers can use Conda, venv, or other tools
- Install dependencies: `pip install -e ".[all]"` or `uv pip install -e ".[all]"`
- Python version: 3.12 (see `.python-version`)

## Coding Standards

### Header Documentation
Use Google-style docstrings for all modules, classes, and functions:

```python
"""Module description.

Longer description if needed.
"""

def function(arg1: str, arg2: int) -> bool:
    """
    Brief description.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Example:
        >>> function("test", 42)
        True
    """
```

### RUFF Lint/Format Style
Configuration in [ruff.toml](./ruff.toml):

- **Line length**: 88 characters (Black-compatible)
- **Target**: Python 3.9+
- **Enabled rules**: Pyflakes (F), pycodestyle errors (E4, E7, E9), isort (I), pydocstyle (D)
- **Pydocstyle**: Google convention
- **Format style**: Double quotes, spaces for indentation, auto line endings
- **Import sorting**: Enabled via isort rules
- **Run**: `make lint` to check and fix, `make lint-cicd` for CI checks

### Docstring Completeness for API Docs

Docstrings are auto-rendered to the MKDocs site via mkdocstrings. Include:

- **Brief description**: First line, imperative mood ("Get passenger by ID")
- **Args**: All parameters with types already in signature
- **Returns**: What the function returns
- **Raises**: All exceptions the function explicitly raises
- **Example**: Runnable doctest when practical

Classes should also document **Attributes** for public instance variables.

Ruff enforces docstring presence via pydocstyle rules (`D` prefix). Run `make lint` to check.

### Code Organization
```
src/app_lib/
├── features/       # Business features (passengers, etc.) — see features/CLAUDE.md
├── common/         # Shared infrastructure (app, auth, utils, lambda handlers) — see common/CLAUDE.md
└── assets/         # Static assets and datasets
```

**Feature-centric layout**: Each feature is self-contained under `features/{name}/` with its own `model/`, `service/`, `routes/`, and `util/`. Features import from `common/`, never from each other.

**Before implementing new functionality**: Check `common/util/` for existing utilities (e.g., `PathUtil` for file paths, `PynamodbUtil` for table naming).

## Tests
- Python Pytest unit tests are located here: [tests/](./tests/)
- See [tests/AGENTS.md](./tests/AGENTS.md) for test organization and conventions
- Run tests: `make test` or `pytest`
