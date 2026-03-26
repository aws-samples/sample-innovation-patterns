# utils/ — IPA Execution Layer

Python CLI utilities invoked by generated Makefiles via `uv run`. Managed by uv.

## Commands

Three entry points in `[project.scripts]`. All invoked as `uv run <command> <subcommand>`.

### deploy — CloudFormation Stack Operations

| Command | What It Does |
|---------|-------------|
| `uv run deploy cfn --stack-name X --template Y` | Create or update a CFN stack |
| `uv run deploy cfn-delete --stack-name X` | Delete a CFN stack |
| `uv run deploy cfn-outputs --stack-name X` | Get stack outputs (for inter-stack wiring) |
| `uv run deploy cfn-outputs --stack-name X --output-key K` | Get single output value |
| `uv run deploy cfn-status --stack-name X` | Check stack existence and status |
| `uv run deploy cfn-events --stack-name X` | Read recent stack events |
| `uv run deploy cfn-list --namespace X --env Y` | List IPA-managed stacks |
| `uv run deploy cfn-generate --template-type security ...` | Generate dynamic CFN template |

Common options: `--region`, `--profile`, `--wait/--no-wait`

### build — Application Build Operations

| Command | What It Does |
|---------|-------------|
| `uv run build docker --tag X` | Build Docker image |
| `uv run build docker --tag X --ecr-repo URI` | Build and push to ECR |

### test — Test Execution

| Command | What It Does |
|---------|-------------|
| `uv run test unit` | Run pytest unit tests |
| `uv run test security` | Run ASH security scans |
| `uv run test cfn-lint --template X` | Validate CFN template |
| `uv run test cfn-lint --directory infra/cfn/` | Validate all templates |

## Module Map

```
utils/
├── pyproject.toml              # Package config, dependencies, entry points
├── ipa_utils/                  # Library package — DO NOT rename
│   ├── __init__.py
│   ├── cli/                    # CLI entry points (click groups)
│   │   ├── deploy.py           # deploy command group (cfn, cfn-delete, cfn-outputs, cfn-status, cfn-events, cfn-list, cfn-generate)
│   │   ├── build.py            # build command group (docker)
│   │   └── test_cmd.py         # test command group (unit, security, cfn-lint)
│   ├── aws/                    # AWS service wrappers (boto3)
│   │   ├── cloudformation.py   # CFN API operations
│   │   ├── ecr.py              # ECR auth and push
│   │   └── cfn_template.py     # Dynamic template generation
│   └── helpers/                # Shared utilities
│       └── output.py           # Stdout/stderr formatting
├── tests/                      # pytest tests
│   ├── conftest.py             # Shared fixtures (moto mocks, CliRunner)
│   ├── fixtures/               # Test data (simple-stack.yml)
│   ├── test_deploy_cfn.py      # create/update stack tests
│   ├── test_deploy_cfn_delete.py
│   ├── test_deploy_cfn_outputs.py
│   ├── test_deploy_cfn_status.py
│   ├── test_deploy_cfn_events.py
│   ├── test_deploy_cfn_list.py
│   ├── test_deploy_cfn_generate.py
│   ├── test_deploy_cli.py      # CLI integration tests
│   ├── test_build_docker.py
│   ├── test_test_unit.py
│   ├── test_test_security.py
│   └── test_test_cfn_lint.py
├── CLAUDE.md                   # THIS FILE — agent quick reference
└── README.md                   # Human-readable documentation
```

## Editability Rules

| Path | Editable? | Notes |
|------|-----------|-------|
| `ipa_utils/cli/*.py` | Yes | CLI routing — add subcommands here |
| `ipa_utils/aws/*.py` | Carefully | Core AWS operations — changes affect all commands |
| `ipa_utils/helpers/*.py` | Yes | Shared utilities |
| `tests/*.py` | Yes | Add tests for new commands |
| `pyproject.toml` | Yes | Add dependencies, entry points |

## Conventions

- **CLI framework**: click (`@click.group()` for command groups)
- **AWS SDK**: boto3 only — no AWS CLI subprocess calls (except ECR login)
- **Credentials**: Never read `.env`. Use `--profile` option or boto3 default chain
- **Exit codes**: 0 = success, 1 = failure (Makefiles depend on this)
- **Output**: Results to stdout, errors to stderr, progress to stderr
- **Testing**: moto for AWS mocking, click.testing.CliRunner for CLI tests
- **Type hints**: Required on all functions (project-wide constraint)
- **CLI ↔ Library separation**: Thin CLI layer in `cli/`, business logic in `aws/`

## Error Handling

All commands print actionable error messages:
- Stack not found → "Stack 'X' does not exist. Deploy it first with: uv run deploy cfn --stack-name X --template Y"
- Permission denied → "Access denied for CloudFormation operation. Re-run /ipa.security to update IAM roles"
- Template invalid → "Template validation failed. Run: uv run test cfn-lint --template Y"
- Timeout → "Timeout waiting for stack 'X'. Check events: uv run deploy cfn-events --stack-name X"

## Dependencies

Runtime: boto3, click, pyyaml, cfn-lint
Dev: pytest, moto, pytest-cov
External: Docker CLI (for build docker), ASH (for test security)
