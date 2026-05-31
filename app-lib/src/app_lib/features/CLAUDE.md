# features/

Business features. Each feature is a self-contained directory under `features/`.

- Features import from `common/`, never from each other.
- To register: 2 lines in `common/app.py` (import router + `app.include_router`).
- To remove: delete the feature directory, remove those 2 lines, delete `tests/features/{name}/`.
- Use `passengers/` as the reference implementation — copy and adapt it.

See README.md for detailed conventions. See `passengers/CLAUDE.md` for an annotated example.

## Feature Layout

```
features/{name}/
├── __init__.py       # Docstring: what this feature does, how to remove it
├── model/            # PynamoDB models — use PynamodbUtil.env_table_name()
├── service/          # Business logic — extend AbstractDataService[T] from common.data
├── routes/           # FastAPI router (APIRouter with prefix="/api/v1") + Pydantic DTOs
└── util/             # Feature-specific utilities (optional)
```

## How to Add a New Feature

### Step 1: Create the directory structure

```
features/{name}/
├── __init__.py
├── model/
│   ├── __init__.py
│   └── {name}_table.py
├── service/
│   ├── __init__.py
│   └── {name}_data_service.py
├── routes/
│   ├── __init__.py
│   ├── {name}_routes.py
│   └── {name}_dto.py
└── util/              # only if needed
    └── __init__.py
```

### Step 2: Define the PynamoDB model

```python
# features/{name}/model/{name}_table.py
from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model

from app_lib.common.util.pynamodb_util import PynamodbUtil


class YourTable(Model):
    class Meta:
        table_name = PynamodbUtil.env_table_name("your_table")

    id = UnicodeAttribute(hash_key=True)
    # ... your attributes
```

### Step 3: Implement the data service

```python
# features/{name}/service/{name}_data_service.py
from app_lib.common.data.abstract_data_service import AbstractDataService
from app_lib.features.{name}.model.{name}_table import YourTable


class YourDataService(AbstractDataService[YourTable]):
    def get(self, id: str):
        try:
            return YourTable.get(id)
        except YourTable.DoesNotExist:
            return None

    def save(self, entity): entity.save()
    def delete(self, id: str): ...
    def list(self, limit=100): return list(YourTable.scan(limit=limit))
    def query(self, limit=100, **filters): ...
    def count(self): return YourTable.count()
```

### Step 4: Create the router and DTOs

```python
# features/{name}/routes/{name}_routes.py
from fastapi import APIRouter
from app_lib.features.{name}.service.{name}_data_service import YourDataService

router = APIRouter(prefix="/api/v1", tags=["{name}"])
data_service = YourDataService()

@router.get("/{name}s")
def list_items(): ...
```

### Step 5: Register in `common/app.py`

Add these 2 lines (alongside the existing passengers import/registration):

```python
from app_lib.features.{name}.routes.{name}_routes import router as {name}_router
# ...
app.include_router({name}_router)
```

### Step 6: Add tests

Create `tests/features/{name}/` mirroring the feature structure with `__init__.py` files.

### Step 7: Infrastructure (if needed)

Enable a DynamoDB table via feature flag in the appropriate tier stack (e.g., `EnablePassengersTable=true` on backend, `EnableJobsTable=true` on queue).

## Feature Isolation (Orchestration-Only Composition)

A feature MUST NOT import from another feature. Cross-feature workflows are
composed at the entry layer (`common/app.py` for REST, `common/lambda/*.py`
for events), never inside features.

Features import from:
- The Python standard library and third-party packages
- `common/*` (shared infrastructure and shared services)
- Their own subdirectories

Features do NOT import from:
- Other features under `features/`
- The composition roots (`common/app.py`, `common/lambda/*.py`)

### Why

Features must be independently understandable, testable, and removable. A
cross-feature import means feature A cannot be reasoned about without also
loading feature B's mental model. Even one such import erodes the property
that gives this layout its value.

### When You Think You Need a Cross-Feature Import

Walk this decision tree:

1. **Feature A needs a type defined in feature B.**
   → Move the type to `common/` (e.g., `common/types/`, `common/data/`).
   Types that cross feature boundaries are not feature-private.

2. **Feature A needs an output value (score, result, report, dict) from feature B.**
   → This is orchestration. Compose at `common/app.py` (REST), `common/lambda/*.py`
   (events), or a CLI entry point. Pass B's output into A as plain data
   (a dict, a Pydantic model from `common/`, a primitive).

3. **Feature A needs to invoke feature B's service.**
   → Same as #2. The invocation belongs at the composition root, not inside A.
   `MyService` accepting `score: float` is the pattern; a `BIntegration` class
   living inside `features/A/` is the anti-pattern.

4. **Feature A needs to extend feature B's behavior.**
   → The abstraction is wrong. Either split B, or define an interface in
   `common/` that both A and B implement.

### Anti-Pattern: Facade-In-Feature

A class inside `features/A/` that wraps `features/B/` is misplaced
orchestration glue. If the class is only called from the composition root
(`common/app.py`, `common/lambda/*.py`, or a CLI), it belongs in `common/`,
not in `features/A/`.

### Examples

✅ Correct — feature accepts plain data, no cross-feature import:

    # features/jobs/service/job_data_service.py
    class JobDataService:
        def save_result(self, job_id: str, result: dict) -> None: ...

✅ Correct — orchestration lives in the composition root:

    # common/lambda/sqs_handler.py  (composition root, MAY import from features)
    from app_lib.features.jobs.service.job_data_service import JobDataService
    from app_lib.features.passengers.service.passenger_data_service import (
        TitanicPassengerDataService,
    )

❌ Wrong — feature importing another feature:

    # features/jobs/service/something.py
    from app_lib.features.passengers.service.passenger_data_service import (
        TitanicPassengerDataService,  # forbidden
    )

### Enforcement

`scripts/lint/check_import_boundaries.py` rejects any
`from app_lib.features.X` import found inside `app_lib/features/Y/` where X≠Y.
Run via `make lint-imports`. Wired into both `make lint` and `make lint-cicd`.

If you find yourself wanting to import another feature, stop and re-read the
Decision Tree above.
