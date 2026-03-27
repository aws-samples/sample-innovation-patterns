# Utility Functions

This directory contains reusable utility functions and helper classes used throughout the application.

## Current Utilities

### PathUtil (`path_util.py`)
Resolves paths relative to library and repository roots. Use for accessing assets, datasets, or other project files.

**Common usage**:
```python
from app_lib.util.path_util import PathUtil

# Get path to assets
assets_dir = PathUtil.assets()
csv_file = PathUtil.assets("datasets/titanic/walkthrough_titanic.csv")

# Get library root
lib_root = PathUtil.lib_root()

# Get repository root
repo_root = PathUtil.repo_root()

# Resolve absolute or relative paths
path = PathUtil.resolve_path("relative/path/to/file")
```

### AgentCoreUtil (`agentcore_util.py`)
AWS Bedrock Agent Core utilities for constructing runtime URLs from agent ARNs.

**Common usage**:
```python
from app_lib.util.agentcore_util import AgentCoreUtil

# Construct runtime URL from agent ARN
arn = "arn:aws:bedrock:us-east-1:123456789012:agent/ABCDEFGHIJ"
url = AgentCoreUtil.runtime_url_from_arn(arn, region="us-east-1")
# Returns: https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/...
```

### PynamodbUtil (`pynamodb_util.py`)
Utilities for PynamoDB model configuration, including environment-aware table naming.

**Common usage**:
```python
from app_lib.util.pynamodb_util import PynamodbUtil

# In a PynamoDB model Meta class:
class Meta:
    table_name = PynamodbUtil.env_table_name("my_table")
    # APP_NAMESPACE unset, APP_ENV unset → "dev_my_table" (default)
    # APP_NAMESPACE unset, APP_ENV="prod" → "prod_my_table"
    # APP_NAMESPACE="acme", APP_ENV="dev" → "acme_dev_my_table"
    # APP_NAMESPACE="acme", APP_ENV="prod" → "acme_prod_my_table"
```

## Adding New Utilities

When adding utilities:
1. Create focused, single-purpose utility modules
2. Add Google-style docstrings with examples
3. Create corresponding tests in `tests/util/`
4. Update this README with usage examples
