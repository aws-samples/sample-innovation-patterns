---
title: Composing a Solution
sidebar_position: 2
---

# Composing a Solution

## Overview

This guide walks through selecting IPA stacks and composing them into a deployable solution using `/ipa.compose`. By the end, the project has generated Makefiles, a security disposition register, and resolved stack parameter wiring — ready for `/ipa.prepare` and `/ipa.deploy`.

## When to Use This Guide

Use this guide when:

- A new IPA project has been initialized with `/ipa.init` and secured with `/ipa.security`, and infrastructure needs to be composed for the first time
- An existing composition needs additional stacks — for example, adding a queue tier to a project that already has frontend and backend
- Stack configuration has changed and the generated Makefiles need to be regenerated
- Understanding what `/ipa.compose` generates is needed before running it

Do not use this guide to deploy infrastructure — see `/ipa.deploy` instead. Do not use this guide to create new stack skills — see `/ipa.author.stack` instead.

## Before You Start

Before you start, confirm the following:

- `/ipa.init` has been completed and `.env` exists with `APP_NAMESPACE`, `APP_ENV`, `AWS_REGION`, `AWS_ACCOUNT_ID`, and `AWS_PROFILE` set
- `/ipa.security` has been completed and IAM roles are provisioned
- AWS CLI is configured with credentials for the target account

## Before / Target State

| Before | After |
|--------|-------|
| Initialized IPA project with `.env` configured and security roles provisioned. No Makefiles, no stack wiring, no deployment artifacts in `scripts/`. | `scripts/` directory populated with `prepare.mk`, `deploy.mk`, `build.mk`, `post-deploy.mk`, `env.mk`, `test.mk`, and `SECURITY-DISPOSITION.md`. Stack parameter wiring resolved across all selected stacks. |

## Steps

### 1. Review available stacks

IPA provides two categories of stacks. Deploy stacks are solution infrastructure deployed and torn down with each environment:

| Stack | Suffix | Resources |
|-------|--------|-----------|
| `ipa.stack.frontend` | `frontend` | S3 bucket, CloudFront distribution with OAC |
| `ipa.stack.backend` | `backend` | Lambda function (container), API Gateway v2 with JWT authorizer, DynamoDB (feature-flagged), CloudWatch dashboard |
| `ipa.stack.queue` | `queue` | SQS queue, dead-letter queue, worker Lambda, DynamoDB (feature-flagged), CloudWatch dashboard |

Prepare stacks are one-time prerequisite infrastructure that persists across deployments:

| Stack | Suffix | Resources |
|-------|--------|-----------|
| `ipa.stack.cognito` | `cognito` | Cognito User Pool, App Client, Hosted UI domain |
| `ipa.stack.ecr` | `ecr` | ECR container image repository |

Prepare stacks are included automatically when a deploy stack requires them. There is no need to select them manually.

### 2. Run `/ipa.compose`

To compose a solution, invoke the compose skill with one or more stack tier names:

```
/ipa.compose frontend backend
```

To compose all three tiers — for example, a full-stack application with background job processing:

```
/ipa.compose frontend backend queue
```

If no stack names are provided, `/ipa.compose` displays a selection menu listing available stacks with their descriptions.

The skill validates that the required `.env` variables are set, reads the stack skills, resolves parameter wiring, and displays a composition summary:

```
Composition Summary: backend + frontend
Project: myapp | Environment: dev | Region: us-east-1

Stack Inventory:
  | Stack              | Suffix   | Template                        | Lifecycle |
  | ipa.stack.cognito  | cognito  | infra/cfn/cognito/cognito.yml   | prepare   |
  | ipa.stack.ecr      | ecr      | infra/cfn/ecr/ecr.yml           | prepare   |
  | ipa.stack.backend  | backend  | infra/cfn/backend/backend.yml   | deploy    |
  | ipa.stack.frontend | frontend | infra/cfn/frontend/frontend.yml | deploy    |

Artifacts to generate:
  - scripts/prepare.mk
  - scripts/deploy.mk
  - scripts/build.mk
  - scripts/post-deploy.mk
  - scripts/env.mk
  - scripts/test.mk
  - scripts/SECURITY-DISPOSITION.md
```

The skill then generates all artifacts and reports completion.

:::note
Running `/ipa.compose` is idempotent. Re-running it regenerates all Makefiles from the current stack definitions. Custom dispositions in `SECURITY-DISPOSITION.md` are preserved across re-composition.
:::

### 3. Review generated Makefiles

After composition, the `scripts/` directory contains six Makefiles and a security register. Each file controls a distinct phase of the deployment lifecycle:

| File | Purpose | Key Targets |
|------|---------|-------------|
| `prepare.mk` | Deploy one-time prerequisite stacks (Cognito, ECR) | `prepare`, `prepare-cognito`, `prepare-ecr` |
| `build.mk` | Build container images and frontend bundle | `build`, `build-fn`, `build-frontend` |
| `deploy.mk` | Deploy solution stacks in dependency order | `deploy`, `deploy-backend`, `deploy-frontend`, `teardown` |
| `post-deploy.mk` | Post-deployment wiring (CORS, Cognito callbacks, frontend upload) | `post-deploy`, `configure-frontend`, `upload-frontend` |
| `env.mk` | Sync deployed stack outputs to `.env` for local development | `update-env`, `update-env-cognito`, `update-env-ecr` |
| `test.mk` | Run tests (stub — placeholder for project-specific tests) | `test` |

To verify that a generated Makefile parses correctly without executing any commands, run a dry run against it:

```bash
make -f scripts/deploy.mk deploy --dry-run
```

The output lists the `aws cloudformation deploy` commands that would execute, with resolved stack names and parameter overrides. No errors should appear.

### 4. Review stack wiring

The composition engine resolves cross-stack dependencies by wiring outputs from one stack into parameters of another. This wiring appears in the generated Makefiles as `$(eval)` lines that query CloudFormation stack outputs at deploy time.

For a frontend + backend composition, the wiring resolves these connections:

| Source Stack | Output | Target Stack | Parameter |
|--------------|--------|--------------|-----------|
| `ecr` | `RepositoryUri` | `backend` | `ImageUri` |
| `cognito` | `IssuerUrl` | `backend` | `AuthIssuer` |
| `cognito` | `UserPoolClientId` | `backend` | `AuthAudience` |
| `security` | `LogBucketName` | `frontend` | `LogBucketDomainName` |

In `scripts/deploy.mk`, the backend deploy target resolves the ECR repository URI and Cognito issuer URL before passing them as `--parameter-overrides` to `aws cloudformation deploy`:

```makefile
deploy-backend:
	$(eval REPOSITORY_URI := $(shell aws cloudformation describe-stacks \
		--stack-name $(APP_NAMESPACE)-$(APP_ENV)-ecr \
		--query 'Stacks[0].Outputs[?OutputKey==`RepositoryUri`].OutputValue' \
		--output text ...))
	$(eval ISSUER_URL := $(shell aws cloudformation describe-stacks \
		--stack-name $(APP_NAMESPACE)-$(APP_ENV)-cognito \
		--query 'Stacks[0].Outputs[?OutputKey==`IssuerUrl`].OutputValue' \
		--output text ...))
	aws cloudformation deploy \
		--stack-name $(APP_NAMESPACE)-$(APP_ENV)-backend \
		--template-file infra/cfn/backend/backend.yml \
		--parameter-overrides Namespace=$(APP_NAMESPACE) Environment=$(APP_ENV) \
			ImageUri=$(REPOSITORY_URI):$(IMAGE_TAG) \
			AuthIssuer=$(ISSUER_URL) \
		--no-fail-on-empty-changeset
```

When composing additional stacks, additional wiring entries are merged. Adding the `queue` stack to a composition that already has `frontend` and `backend` adds wiring from the queue stack to the backend and enables the SQS integration feature flag:

| Source Stack | Output | Target Stack | Parameter |
|--------------|--------|--------------|-----------|
| `queue` | `QueueUrl` | `backend` | `SqsQueueUrl` |
| `queue` | `QueueArn` | `backend` | `SqsSendQueueArns` |

The backend stack also receives `EnableSqsIntegration=true` to activate SQS send permissions on the Lambda execution role.

### 5. Review the security disposition register

The composition generates `scripts/SECURITY-DISPOSITION.md`, a register of known security findings accepted for the current scope. Each stack declares known deferrals — security findings that are intentionally accepted with documented rationale.

The register contains two sections:

- **Stack Deferrals** — security findings inherited from the composed stacks, regenerated on each composition
- **Custom Dispositions** — project-specific findings added manually, preserved across re-composition

Example deferrals from a frontend + backend composition:

| ID | Finding | Disposition | Rationale |
|----|---------|-------------|-----------|
| S3-1 | No bucket versioning | Accepted — POC scope | POC scope |
| CF-1 | No custom domain / ACM certificate | Accepted — POC scope | Uses *.cloudfront.net |
| APIGW-1 | CORS origin `*` during initial deploy | Accepted — POC scope | CloudFront domain unknown at API deploy time; auto-wired in post-deploy |

Review this register before handing the project to a customer. Each deferral should be resolved or accepted with stakeholder sign-off for production deployments.

### 6. Optional: Add stacks to an existing composition

To add a stack to an existing composition, re-run `/ipa.compose` with all stack names — both existing and new. For example, to add background job processing to a project that already has frontend and backend:

```
/ipa.compose frontend backend queue
```

The skill detects the existing composition, merges the new stacks with the existing ones, and regenerates all Makefiles. The regeneration is idempotent — existing configuration is preserved.

:::warning
Do not edit the generated Makefiles manually. Re-running `/ipa.compose` overwrites all Makefiles in `scripts/`. If the skill detects a malformed header in `deploy.mk` indicating manual edits, it warns before proceeding.
:::

## Verification

To confirm that the composition completed successfully:

1. Verify that all expected artifacts exist in `scripts/`:

   ```bash
   ls scripts/*.mk scripts/SECURITY-DISPOSITION.md
   ```

   Expected output:

   ```
   scripts/build.mk
   scripts/deploy.mk
   scripts/env.mk
   scripts/post-deploy.mk
   scripts/prepare.mk
   scripts/test.mk
   scripts/SECURITY-DISPOSITION.md
   ```

2. Verify that the deploy Makefile parses without errors:

   ```bash
   make -f scripts/deploy.mk deploy --dry-run
   ```

   The output lists `aws cloudformation deploy` commands with resolved stack names and parameter overrides.

3. Verify that `SECURITY-DISPOSITION.md` references the composed stacks:

   ```bash
   head -3 scripts/SECURITY-DISPOSITION.md
   ```

   Expected output:

   ```
   # Security Disposition Register: backend + frontend
   ```

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `/ipa.compose` fails with missing `.env` variable error | One or more of `APP_NAMESPACE`, `APP_ENV`, `AWS_REGION`, or `AWS_ACCOUNT_ID` is not set in `.env` | Run `/ipa.init` to generate the `.env` file with all required variables |
| Re-composition overwrites manual Makefile edits | `/ipa.compose` regenerates all Makefiles from stack definitions on every run | Do not edit generated Makefiles manually — for custom targets, create a separate Makefile that includes the generated ones |
| Stack not found when running `/ipa.compose {name}` | The stack name does not match a known stack skill in `.claude/skills/ipa.stack.*` | Run `/ipa.compose` without arguments to see available stacks and select from the menu |

## Next Steps

- **Deploy prerequisite stacks** — run `/ipa.prepare` to deploy Cognito, ECR, and other prepare-lifecycle stacks
- **Build and deploy** — run `/ipa.deploy` to build artifacts and deploy all solution stacks
- **Stack reference** — see the Stacks section for per-stack parameters, outputs, and architecture diagrams
- **Tear down infrastructure** — run `/ipa.destroy` to delete deployed stacks
