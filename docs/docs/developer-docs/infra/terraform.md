---
title: Terraform IaC Support
sidebar_position: 2
---

# Terraform IaC Support

Terraform is an alternative IaC engine available alongside CloudFormation. When `APP_IAC=terraform` is set in `.env` (selected during `/ipa-init`), `/ipa-compose` generates Makefile targets that execute `terraform init/apply/destroy` instead of `aws cloudformation deploy/delete-stack`.

Both engines produce functionally equivalent infrastructure. The Terraform modules mirror the CloudFormation templates 1:1 in resources, parameters, and outputs.

## How It Works

### IaC Mode Selection

The builder chooses the IaC tool during `/ipa-init` (5th question). The choice is stored as `APP_IAC=terraform` in `.env` and read by `/ipa-compose` at Step 6.0 to determine which Makefile template set to use.

### State Backend Bootstrap

Terraform requires a state backend before any module can run. IPA solves this chicken-and-egg problem by deploying the state backend via CloudFormation — always, even in full-TF mode:

```
infra/cfn/tfstate/tfstate.yml → S3 bucket + DynamoDB lock table
```

The `prepare-tfstate` target in `scripts/prepare.mk` is the only CFN target in a Terraform-mode project. After deployment, `env.mk` writes `TF_STATE_BUCKET` and `TF_STATE_LOCK_TABLE` to `.env` for all subsequent Terraform operations.

### Module Architecture

Each Terraform module is a **flat, independent root module** under `infra/tf/{tier}/`:

```
infra/tf/backend/
├── main.tf          # Resource definitions
├── variables.tf     # Input variables with validation
├── outputs.tf       # Exported values
└── versions.tf      # Provider + backend configuration
```

Modules are self-contained — no shared modules, no abstractions, no code generation. A customer engineer can fork and evolve any module without IPA knowledge.

### Cross-Module Wiring

IPA uses two wiring patterns depending on the source module's lifecycle:

| Source Lifecycle | Wiring Mechanism | Example |
|-----------------|------------------|---------|
| **prepare** → deploy | `terraform_remote_state` data source in the consuming module | `cognito` → `backend` (issuer_url, client_id) |
| **deploy** → deploy | Makefile subshell `$$(cd ../queue && terraform output -raw queue_url)` | `queue` → `backend` (queue_url, queue_arn) |

The prepare→deploy pattern embeds a `terraform_remote_state` data source that reads the prepare module's state from S3:

```hcl
data "terraform_remote_state" "cognito" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "${var.namespace}-${var.environment}/cognito/terraform.tfstate"
    region = var.region
  }
}
```

The deploy→deploy pattern uses Makefile-level wiring because both modules deploy in the same `make` invocation — the consuming module's `terraform_remote_state` would fail if the source module has no state yet:

```makefile
deploy-backend: deploy-queue
	cd infra/tf/backend && \
	terraform init -input=false -reconfigure ... && \
	terraform apply -auto-approve -input=false \
		... \
		-var="sqs_queue_url=$$(cd ../queue && terraform output -raw queue_url)"
```

### env.mk in Terraform Mode

In Terraform mode, `env.mk` uses `terraform output -raw` from each module directory instead of `aws cloudformation describe-stacks`:

```makefile
update-env-cognito:
	$(eval OIDC_ISSUER_VAL := $(shell cd infra/tf/cognito && terraform output -raw issuer_url 2>/dev/null || echo ""))
	# ... writes to .env
```

The one exception is `update-env-tfstate`, which queries the CFN stack via `describe-stacks` (the tfstate stack is always CloudFormation).

## Usage

### Selecting Terraform During Init

```
/ipa-init
```

At the 5th question ("Which infrastructure-as-code tool?"), select **terraform**.

### Compose and Deploy

The workflow is identical to CloudFormation mode — only the underlying commands change:

```bash
/ipa-compose backend frontend queue    # generates TF-mode Makefiles
/ipa-prepare                           # deploys tfstate (CFN) + cognito/ecr/logs (TF)
/ipa-deploy                            # deploys backend/frontend/queue (TF)
```

### Validating Modules

```bash
make -f scripts/test.mk validate
```

Runs `terraform init -backend=false && terraform validate` in each `infra/tf/*/` directory.

## Extending / Maintaining

### Adding a Variable to a Module

1. Add the variable to `infra/tf/{tier}/variables.tf` with type, description, and validation.
2. Reference it in `main.tf`.
3. Update the stack skill's `## Terraform Module` → Variables table.
4. Re-run `/ipa-compose` to regenerate Makefiles with the new `-var=` override.

### Adding a New Resource to a Module

1. Add the resource to `infra/tf/{tier}/main.tf`.
2. If it produces values needed downstream, add an output to `outputs.tf`.
3. Run `terraform validate` in the module directory.
4. Update the stack skill's Terraform Module section if outputs changed.

### Feature Flags

Terraform uses `count = var.enable_x ? 1 : 0` as the equivalent of CloudFormation Conditions:

```hcl
resource "aws_dynamodb_table" "passengers" {
  count    = var.enable_passengers_table ? 1 : 0
  name     = "${var.namespace}-${var.environment}-passengers"
  # ...
}
```

Conditional outputs reference the resource with an index:

```hcl
output "passengers_table_arn" {
  value = var.enable_passengers_table ? aws_dynamodb_table.passengers[0].arn : ""
}
```

### State Key Convention

All modules store state under the pattern:

```
{namespace}-{environment}/{tier}/terraform.tfstate
```

For example: `myapp-dev/backend/terraform.tfstate` in the S3 state bucket.

## Known Issues

- **No `terraform import` workflow** — modules support new deployments only. Migrating existing CFN-deployed infrastructure to Terraform is not automated.
- **No CloudWatch observability** — per the 016-remove-cloudwatch-observability feature, TF modules omit dashboards and alarms. Log groups are retained.
- **Security stack always uses CFN** — `/ipa-security` generates `infra/cfn/generated/iam.yml` regardless of `APP_IAC`. Security IAM roles are referenced via `.env` variables.

## References

- `infra/cfn/tfstate/tfstate.yml` — state backend CloudFormation template
- `.claude/skills/ipa-stack-tfstate/SKILL.md` — tfstate prepare stack skill
- `.claude/skills/ipa-compose/MAKEFILE_TEMPLATES.md` → Terraform Mode Templates section
- [Terraform S3 Backend documentation](https://developer.hashicorp.com/terraform/language/settings/backends/s3)
