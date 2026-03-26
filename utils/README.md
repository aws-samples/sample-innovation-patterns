# IPA Utilities

Python CLI utilities for building, testing, and deploying AWS infrastructure. These utilities are the execution layer invoked by IPA-generated Makefiles and can also be run directly.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- AWS CLI v2 (for ECR authentication)
- Docker (for container image builds)

## Installation

```bash
cd utils/
uv sync
```

This installs all dependencies into `utils/.venv/` and registers the CLI entry points.

## Quick Reference

| Command | Description |
|---------|-------------|
| `uv run deploy cfn` | Create or update a CloudFormation stack |
| `uv run deploy cfn-delete` | Delete a CloudFormation stack |
| `uv run deploy cfn-outputs` | Retrieve stack outputs |
| `uv run deploy cfn-status` | Check stack status |
| `uv run deploy cfn-events` | Read stack events |
| `uv run deploy cfn-generate` | Generate a dynamic CloudFormation template |
| `uv run build docker` | Build and optionally push a Docker image |
| `uv run test unit` | Run unit tests |
| `uv run test security` | Run security scans (ASH) |
| `uv run test cfn-lint` | Validate CloudFormation templates |

## Commands

### deploy cfn — Create or Update a Stack

Deploy a CloudFormation stack. If the stack does not exist, it is created. If it exists, it is updated (no-op if no changes detected).

```bash
uv run deploy cfn \
    --stack-name myproject-dev-dynamodb \
    --template infra/cfn/dynamodb.yml \
    --parameter-overrides TableName=myproject-dev-dynamodb \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--stack-name` | Yes | — | CloudFormation stack name |
| `--template` | Yes | — | Path to CloudFormation YAML template |
| `--parameter-overrides` | No | — | Space-separated Key=Value parameter pairs |
| `--capabilities` | No | — | CloudFormation capabilities (e.g., CAPABILITY_NAMED_IAM) |
| `--region` | No | AWS_DEFAULT_REGION | AWS region for the operation |
| `--profile` | No | default credential chain | AWS CLI profile name |
| `--wait / --no-wait` | No | --wait | Wait for the operation to complete |
| `--tags` | No | — | Space-separated Key=Value tag pairs |

**Behavior:**
- Checks if the stack exists before deciding create vs. update
- If the stack is in ROLLBACK_COMPLETE state, deletes and recreates
- Polls stack status until terminal state when `--wait` is set
- Prints stack outputs on successful completion

### deploy cfn-delete — Delete a Stack

```bash
uv run deploy cfn-delete --stack-name myproject-dev-dynamodb --region us-east-1
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--stack-name` | Yes | — | Stack to delete |
| `--region` | No | AWS_DEFAULT_REGION | AWS region |
| `--profile` | No | default chain | AWS CLI profile |
| `--wait / --no-wait` | No | --wait | Wait for deletion |

### deploy cfn-outputs — Retrieve Stack Outputs

Query the outputs of a deployed CloudFormation stack. Used for inter-stack parameter wiring.

```bash
# Get all outputs
uv run deploy cfn-outputs --stack-name myproject-dev-cognito

# Get a specific output value (raw, for Makefile shell capture)
uv run deploy cfn-outputs --stack-name myproject-dev-cognito --output-key UserPoolArn

# Output as KEY=VALUE format
uv run deploy cfn-outputs --stack-name myproject-dev-cognito --format env
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--stack-name` | Yes | — | Stack to query |
| `--output-key` | No | — | Specific output key (prints all if omitted) |
| `--region` | No | AWS_DEFAULT_REGION | AWS region |
| `--profile` | No | default chain | AWS CLI profile |
| `--format` | No | text | Output format: `text`, `json`, `env` |

### deploy cfn-status — Check Stack Status

```bash
uv run deploy cfn-status --stack-name myproject-dev-dynamodb --region us-east-1
```

Prints status string (e.g., `CREATE_COMPLETE`, `DOES_NOT_EXIST`). Exit 0 if stack exists, exit 1 if not.

### deploy cfn-events — Read Stack Events

```bash
uv run deploy cfn-events --stack-name myproject-dev-dynamodb --limit 20 --region us-east-1
```

Prints recent stack events as a table: Timestamp, LogicalResourceId, Status, StatusReason.

### deploy cfn-generate — Generate Dynamic Template

Generate a CloudFormation template at runtime for security-sensitive configurations.

```bash
uv run deploy cfn-generate \
    --template-type security \
    --managed-policy AdministratorAccess \
    --namespace myproject \
    --env dev \
    --account-id 123456789012 \
    --output infra/cfn/generated/security.yml
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--template-type` | Yes | — | Template type (`security`) |
| `--namespace` | Yes | — | Project namespace |
| `--env` | Yes | — | Environment (dev/staging/prod) |
| `--account-id` | Yes | — | 12-digit AWS account ID |
| `--output` | Yes | — | Output file path |
| `--managed-policy` | No | ReadOnlyAccess | AWS managed policy name |
| `--role-arn` | No | — | Existing role ARN (skip role creation) |

### build docker — Build and Push Docker Image

```bash
# Build only
uv run build docker --tag myproject-dev-lambda --dockerfile backend/Dockerfile --context backend/

# Build and push to ECR
uv run build docker \
    --tag myproject-dev-lambda \
    --ecr-repo 123456789012.dkr.ecr.us-east-1.amazonaws.com/myproject-dev-lambda \
    --region us-east-1
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--tag` | Yes | — | Image tag name |
| `--dockerfile` | No | Dockerfile | Path to Dockerfile |
| `--context` | No | . | Docker build context directory |
| `--ecr-repo` | No | — | ECR repository URI (authenticates and pushes if provided) |
| `--region` | No | AWS_DEFAULT_REGION | AWS region (for ECR auth) |
| `--profile` | No | default chain | AWS CLI profile (for ECR auth) |
| `--platform` | No | linux/amd64 | Target platform |
| `--build-arg` | No | — | Build arguments (repeatable) |

### test unit — Run Unit Tests

```bash
uv run test unit --path tests/ --verbose --coverage
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--path` | No | tests/ | Test directory or file |
| `--markers` | No | — | Pytest marker expression |
| `--verbose` | No | false | Verbose output |
| `--coverage` | No | false | Collect coverage |

### test security — Run Security Scans

```bash
uv run test security --target infra/cfn/ --format json
```

Requires [ASH (Automated Security Helper)](https://github.com/awslabs/automated-security-helper) to be installed.

### test cfn-lint — Validate CloudFormation Templates

```bash
# Validate a specific template
uv run test cfn-lint --template infra/cfn/dynamodb.yml

# Validate all templates in a directory
uv run test cfn-lint --directory infra/cfn/
```

## Architecture

```
utils/
├── pyproject.toml          # Package definition and entry points
├── ipa_utils/              # Main package
│   ├── cli/                # Click-based CLI entry points
│   │   ├── deploy.py       # deploy command group
│   │   ├── build.py        # build command group
│   │   └── test_cmd.py     # test command group
│   ├── aws/                # AWS service wrapper modules
│   │   ├── cloudformation.py  # CFN API operations
│   │   ├── ecr.py             # ECR auth and push
│   │   └── cfn_template.py    # Dynamic template generation
│   └── helpers/            # Shared utilities
│       └── output.py       # Stdout/stderr formatting
├── tests/                  # pytest test suite
│   ├── conftest.py         # Shared fixtures
│   └── fixtures/           # Test data
└── README.md               # This file
```

### How These Commands Are Used

IPA generates Makefiles (e.g., `scripts/deploy.mk`) that invoke these utilities:

```makefile
deploy-dynamodb:
	uv run deploy cfn \
		--stack-name $(NAMESPACE)-$(APP_ENV)-dynamodb \
		--template infra/cfn/dynamodb.yml

deploy-lambda: deploy-dynamodb deploy-cognito
	$(eval TABLE := $(shell uv run deploy cfn-outputs --stack-name $(NAMESPACE)-$(APP_ENV)-dynamodb --output-key TableName))
	uv run deploy cfn \
		--stack-name $(NAMESPACE)-$(APP_ENV)-lambda \
		--template infra/cfn/lambda.yml \
		--parameter-overrides TableName=$(TABLE)
```

The same commands work identically when run locally (using your AWS profile) or in CI/CD (using the CodeBuild execution role's default credential chain).

## Credential Resolution

These utilities never read `.env` or manage AWS credentials directly. Credentials are resolved by boto3's standard credential chain:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS CLI profile (via `--profile` option or `AWS_PROFILE` env var)
3. Instance/container role (CodeBuild execution role in CI/CD)

## Development

### Running Tests

```bash
cd utils/
uv run pytest tests/ -v
```

### Adding a New Command

1. Add a new function to the appropriate CLI module (`ipa_utils/cli/deploy.py`, etc.)
2. Decorate with `@<group>.command()`
3. Add business logic in `ipa_utils/aws/` (keep CLI layer thin)
4. Add corresponding test in `tests/`
5. Update CLAUDE.md and this README

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Operation completed successfully |
| 1 | Operation failed (error message printed to stderr) |

All commands provide actionable error messages that suggest next steps.
