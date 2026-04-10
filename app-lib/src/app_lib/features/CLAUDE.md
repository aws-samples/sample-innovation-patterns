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

## Firewall Rule

- Features may import from `common/*`
- Features may import from their own subdirectories
- Features MUST NOT import from other features
