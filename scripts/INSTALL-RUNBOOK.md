# Install Runbook

Step-by-step guide to deploying an IPA-composed project. These instructions work for any composition — the Makefiles encode the specific stacks and parameters for your project.

## Prerequisites

- AWS CLI v2 installed and configured
- GNU Make
- Docker (if your composition includes container builds)
- [ASH (Automated Security Helper)](https://github.com/awslabs/automated-security-helper) (for security scanning)
- An AWS account with permissions to deploy CloudFormation stacks, create IAM roles, and manage the services in your composition

## 1. Configure Environment

Copy the template and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your AWS account details:

| Variable | Description | Example |
|---|---|---|
| `AWS_PROFILE` | AWS CLI profile name (omit to use default credential chain) | `my-profile-Admin` |
| `AWS_REGION` | Target AWS region | `us-east-1` |
| `AWS_ACCOUNT_ID` | 12-digit AWS account ID | `123456789012` |
| `APP_NAMESPACE` | Project name prefix for stack naming (max 12 chars, lowercase) | `myapp` |
| `APP_ENV` | Environment name | `dev` |

The security variables (`APP_BUILDER_ROLE_ARN`, `APP_CODEBUILD_ROLE_ARN`) are populated by `/ipa.security` or can be set manually if you have pre-provisioned roles.

## 2. Verify AWS Credentials

Confirm you can reach the target account:

```bash
aws sts get-caller-identity
```

The `Account` field should match your `AWS_ACCOUNT_ID`.

## 3. Validate Templates

Run template validation and security scans before deploying anything:

```bash
make -f scripts/test.mk test
```

This runs two checks:

| Target | What it does |
|---|---|
| `test-validate` | Validates all CloudFormation templates with `aws cloudformation validate-template` |
| `test-security` | Runs ASH security scanner against `infra/` |

Run individual checks:

```bash
make -f scripts/test.mk test-validate    # templates only
make -f scripts/test.mk test-security    # security only
```

## 4. Deploy Prepare Stacks (One-Time)

Prepare stacks are infrastructure prerequisites that must exist before the main deployment. These are typically long-lived resources like ECR repositories.

```bash
make -f scripts/prepare.mk prepare
```

Run this once per environment. Re-run only when prepare targets change (e.g., after adding a new stack via `/ipa.compose`).

Verify the stacks completed:

```bash
aws cloudformation describe-stacks \
    --query "Stacks[?contains(StackName, '$(grep APP_NAMESPACE .env | cut -d= -f2)')].{Name:StackName,Status:StackStatus}" \
    --output table
```

## 5. Build Artifacts

Build container images, frontend bundles, or other artifacts required by the deploy stacks:

```bash
make -f scripts/build.mk build
```

If your composition has no build targets, this is a no-op. Skip to step 6.

For compositions with container builds, Docker must be running and you need ECR access. The build Makefile handles ECR authentication and push automatically.

## 6. Deploy Stacks

Deploy all infrastructure stacks in dependency order:

```bash
make -f scripts/deploy.mk deploy
```

The Makefile encodes stack ordering — dependencies deploy first. Each target uses `--no-fail-on-empty-changeset`, so re-running is safe (idempotent).

Deploy a single stack by name:

```bash
make -f scripts/deploy.mk deploy-<stack-name>
```

Check that all stacks reached a successful state:

```bash
aws cloudformation list-stacks \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
    --query "StackSummaries[?contains(StackName, '$(grep APP_NAMESPACE .env | cut -d= -f2)')].{Name:StackName,Status:StackStatus}" \
    --output table
```

## 7. Post-Deploy Verification

After deployment, retrieve stack outputs for your application configuration:

```bash
aws cloudformation describe-stacks \
    --stack-name <namespace>-<env>-<stack> \
    --query "Stacks[0].Outputs" \
    --output table
```

Stack names follow the pattern `{APP_NAMESPACE}-{APP_ENV}-{service}` (e.g., `myapp-dev-cognito`).

## Teardown

### Tear Down Deploy Stacks

Deletes stacks deployed by `deploy.mk` in reverse dependency order:

```bash
make -f scripts/deploy.mk teardown
```

Or tear down a single stack:

```bash
make -f scripts/deploy.mk teardown-<stack-name>
```

Each teardown target waits for deletion to complete before proceeding.

### Tear Down Prepare Stacks

Prepare stacks are **not** removed by the deploy teardown. Remove them separately when you no longer need the environment:

```bash
make -f scripts/prepare.mk teardown-prepare
```

**Warning:** Prepare stacks may contain data (e.g., ECR images). Verify they are safe to delete.

## Troubleshooting

### Stack stuck in `*_IN_PROGRESS`

Wait for it to finish, or check the CloudFormation console for events:

```bash
aws cloudformation describe-stack-events \
    --stack-name <stack-name> \
    --query "StackEvents[:5].{Time:Timestamp,Status:ResourceStatus,Reason:ResourceStatusReason}" \
    --output table
```

### Stack in `ROLLBACK_COMPLETE`

The stack failed to create. Delete it before retrying:

```bash
aws cloudformation delete-stack --stack-name <stack-name>
aws cloudformation wait stack-delete-complete --stack-name <stack-name>
```

Then re-run the relevant `make` target.

### `UPDATE_ROLLBACK_COMPLETE`

The stack exists but an update failed. Re-running `make -f scripts/deploy.mk deploy-<stack>` will attempt the update again. Fix the underlying issue first (check stack events).

### `.env` not found or variables empty

All Makefiles load `.env` via `-include .env`. Confirm the file exists at the project root and contains the required variables. Use `.env.example` as a reference.

## Quick Reference

| Step | Command | When to run |
|---|---|---|
| Validate | `make -f scripts/test.mk test` | Before every deploy |
| Prepare | `make -f scripts/prepare.mk prepare` | Once per environment |
| Build | `make -f scripts/build.mk build` | Before deploy (if applicable) |
| Deploy | `make -f scripts/deploy.mk deploy` | Each deployment |
| Teardown deploy | `make -f scripts/deploy.mk teardown` | When removing stacks |
| Teardown prepare | `make -f scripts/prepare.mk teardown-prepare` | When decommissioning environment |
