---
name: ipa.destroy
description: "Destroy composed infrastructure patterns by executing teardown targets
  in generated Makefiles. Use when the user says 'destroy', 'tear down', 'delete stacks',
  'remove infrastructure', 'clean up stacks', or invokes /ipa.destroy."
model: opus
---

# /ipa.destroy — Destroy Infrastructure Pattern

This skill tears down a composed infrastructure pattern by executing the teardown targets in generated Makefiles. It validates prerequisites, checks which stacks exist, displays a teardown plan with data loss warnings, requires double confirmation, executes the teardown, verifies deletion, and reports results.

**Prerequisite workflow**: `/ipa.init` → `/ipa.security` → `/ipa.compose` → `/ipa.deploy` → **`/ipa.destroy`**

---

## What This Skill Does

1. Validates prerequisites (.env, Makefiles, AWS credentials, required tools)
2. Checks which pattern stacks currently exist (pre-teardown status)
3. Displays a teardown plan with data loss warnings
4. Requires double confirmation (including typing the namespace)
5. Runs `make -f scripts/deploy.mk teardown` (deletes stacks in reverse dependency order)
6. Verifies all stacks are deleted
7. Reports results

## What This Skill Does NOT Do

- Does not deploy anything — that's `/ipa.deploy`'s job
- Does not ask "deploy or teardown?" — it proceeds directly to teardown
- Does not generate Makefiles — that's `/ipa.compose`'s job
- Does not create or modify IAM roles — that's `/ipa.security`'s job
- Does not read stack SKILL.md files — Makefiles are the only deployment contract
- Does not call AWS APIs directly — delegates to `make` which calls `uv run --project utils deploy cfn-delete`
- Does not delete the security stack — security infrastructure is managed by `/ipa.security`
- Does not delete prepare stacks (ECR, etc.) — prepare infrastructure is managed separately. To tear down prepare stacks manually: `make -f scripts/prepare.mk teardown-prepare`
- Does not support per-stack targeting — always tears down the full pattern via the aggregate target
- Does not modify `.env` — it is a read-only consumer of configuration

## Information Sources

| Source | What Destroy Reads | When |
|--------|-------------------|------|
| `.env` | `APP_NAMESPACE`, `APP_ENV`, `AWS_REGION`, `AWS_PROFILE`, `AWS_ACCOUNT_ID`, `APP_BUILDER_ROLE_ARN` | Pre-flight validation |
| `scripts/deploy.mk` | Teardown target names, stack names, reverse dependency order | Pre-teardown status check + execution |
| `make -n` | Dry-run output showing teardown commands that would execute | Teardown plan display |
| `uv run --project utils deploy cfn-status` | Stack status | Pre-teardown status check + post-teardown verification |
| `uv run --project utils deploy cfn-events` | Stack events | Failure diagnosis |
| `uv run --project utils deploy cfn-list` | All managed stacks | Optional status overview |

---

## Step 1: Pre-Flight Validation

Run **all** checks below and collect results. Report **all** failures at once with per-item remediation — do not stop at the first failure.

### 1.1 Verify .env Exists

Check that `.env` exists at the project root and is non-empty.

**If missing**: "`.env` not found. Run `/ipa.init` to initialize project configuration."

### 1.2 Verify Required .env Variables

Read `.env` and verify these variables exist and are non-empty:

| Variable | Written By | Error If Missing |
|----------|------------|-----------------|
| `APP_NAMESPACE` | `/ipa.init` | "Missing `APP_NAMESPACE`. Run `/ipa.init`." |
| `APP_ENV` | `/ipa.init` | "Missing `APP_ENV`. Run `/ipa.init`." |
| `AWS_REGION` | `/ipa.init` | "Missing `AWS_REGION`. Run `/ipa.init`." |
| `AWS_PROFILE` | `/ipa.init` | "Missing `AWS_PROFILE`. Run `/ipa.init`." |
| `AWS_ACCOUNT_ID` | `/ipa.init` | "Missing `AWS_ACCOUNT_ID`. Run `/ipa.init`." |
| `APP_BUILDER_ROLE_ARN` | `/ipa.security` | "Missing `APP_BUILDER_ROLE_ARN`. Run `/ipa.security`." |

Store all variable values for use in subsequent steps.

### 1.3 Verify Deployment Scripts Exist

Check that `scripts/deploy.mk` exists and contains a `teardown` target.

**If missing**: "`scripts/deploy.mk` not found. Run `/ipa.compose` to generate deployment artifacts."

**If no teardown target**: "`scripts/deploy.mk` has no `teardown` target. Run `/ipa.compose` to regenerate deployment artifacts."

### 1.4 Verify Security Stack Is Deployed

Run:

```bash
uv run --project utils deploy cfn-status --stack-name {APP_NAMESPACE}-{APP_ENV}-security
```

Expected: `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

**If not deployed**: "Security stack `{APP_NAMESPACE}-{APP_ENV}-security` is not deployed. Run `/ipa.security` first."

### 1.5 Verify AWS Credentials

Run:

```bash
aws sts get-caller-identity --profile {AWS_PROFILE} --region {AWS_REGION}
```

**If fails**: "AWS credentials are invalid or expired for profile `{AWS_PROFILE}`. Refresh your credentials and try again."

### 1.6 Verify Make Is Installed

Run `which make`.

**If missing**: "GNU Make is not installed. On macOS it is pre-installed. On Linux: `sudo apt install make`."

### 1.7 Verify uv Is Installed

Run `which uv`.

**If missing**: "`uv` is not installed. Install via: `curl -LsSf https://astral.sh/uv/install.sh | sh`"

### Validation Summary

If **any** checks fail, display all failures in a single summary table and **STOP**:

```
Pre-flight validation failed:

  ✗ .env variable APP_BUILDER_ROLE_ARN missing — Run /ipa.security
  ✗ AWS credentials expired — Refresh credentials for profile {AWS_PROFILE}

Fix the above issues and re-run /ipa.destroy.
```

If **all** checks pass: "Pre-flight validation passed. All prerequisites verified."

---

## Step 2: Pre-Teardown Status Check

Before displaying the teardown plan, check which stacks currently exist. This provides a status-aware plan that shows "will delete" vs "already gone."

### 2.1 Extract Stack Names from deploy.mk

Run `make -n -f scripts/deploy.mk teardown` and extract the `--stack-name` values from the output. These are the stacks that the teardown would target.

### 2.2 Check Each Stack's Current Status

For each stack name extracted above, run:

```bash
uv run --project utils deploy cfn-status --stack-name {stack-name}
```

Categorize each stack:

| Status | Category | Action |
|--------|----------|--------|
| `CREATE_COMPLETE`, `UPDATE_COMPLETE` | Exists | Will be deleted |
| `DOES_NOT_EXIST` (or command returns "stack not found") | Gone | Skip (already deleted) |
| `*_IN_PROGRESS` | Transitioning | Warn builder — stack is mid-operation |
| `ROLLBACK_COMPLETE`, `DELETE_FAILED`, `*_FAILED` | Failed state | Will attempt deletion |

### 2.3 Nothing to Destroy

If **ALL** stacks are in the "Gone" category:

"No pattern stacks to destroy. All stacks have already been deleted."

**STOP** — there is nothing to tear down.

---

## Step 3: Display Teardown Plan + Warnings

### 3.1 Show Status-Aware Plan

Display the teardown plan with each stack's current status and the action that will be taken:

```
⚠️  TEARDOWN PLAN: {APP_NAMESPACE}-{APP_ENV}

  Stack                              Current Status      Action
  ─────────────────────────────────  ──────────────────  ──────
  {APP_NAMESPACE}-{APP_ENV}-lambda   CREATE_COMPLETE     DELETE
  {APP_NAMESPACE}-{APP_ENV}-cognito  CREATE_COMPLETE     DELETE
  {APP_NAMESPACE}-{APP_ENV}-ecr      DOES_NOT_EXIST      skip (already deleted)

WARNING: This will permanently delete all stacks listed above.
Stateful resources (ECR repositories with images, DynamoDB tables with data,
S3 buckets with objects) will be destroyed. This action cannot be undone.
```

### 3.2 Show Dry-Run Commands

Run Make dry-run and display the commands:

```bash
make -n -f scripts/deploy.mk teardown
```

Show the output so the builder can see exactly what commands will execute.

---

## Step 4: Double Confirmation

Teardown is a destructive operation. Require two separate confirmations before proceeding.

### 4.1 First Confirmation

"Are you sure you want to destroy all infrastructure? (yes/no):"

If the builder does not confirm: "Destroy cancelled. No stacks were deleted." **STOP**.

### 4.2 Second Confirmation

"Type the namespace `{APP_NAMESPACE}` to confirm:"

Verify the typed value matches `APP_NAMESPACE` exactly (case-sensitive).

If the value does not match: "Destroy cancelled. Namespace did not match. No stacks were deleted." **STOP**.

---

## Step 5: Execute Teardown

Run:

```bash
make -f scripts/deploy.mk teardown
```

Display Make output as it runs. Each target prints its `uv run` command, providing natural progress indication.

**If teardown succeeds** (exit code = 0): proceed to Step 6.

**If teardown partially fails**: Report which stacks were deleted and which remain:

```
Teardown partially completed:

  ✓ {APP_NAMESPACE}-{APP_ENV}-lambda   — deleted
  ✗ {APP_NAMESPACE}-{APP_ENV}-cognito  — DELETE_FAILED
  · {APP_NAMESPACE}-{APP_ENV}-ecr      — not attempted

Check the failed stack and see the Failure Handling section below.
After fixing the issue, re-run /ipa.destroy — already-deleted stacks will be skipped.
```

**Idempotency**: Re-running `/ipa.destroy` after a partial failure is always safe. The execution layer handles all state transitions:
- Non-existent stack → succeeds silently (already deleted)
- `DELETE_FAILED` → retries deletion
- `*_COMPLETE` → proceeds with deletion

---

## Step 6: Post-Teardown Verification

For each stack in the teardown plan, run:

```bash
uv run --project utils deploy cfn-status --stack-name {stack-name}
```

Confirm all return `DOES_NOT_EXIST` or `DELETE_COMPLETE`.

If any stack still exists with a non-deleted status, report it as part of the completion report.

---

## Step 7: Completion Report

Display a structured report:

```
Destroy Complete: {APP_NAMESPACE}-{APP_ENV}

  All pattern stacks have been deleted:

  ✓ {APP_NAMESPACE}-{APP_ENV}-lambda   — deleted
  ✓ {APP_NAMESPACE}-{APP_ENV}-cognito  — deleted
  · {APP_NAMESPACE}-{APP_ENV}-ecr      — already deleted (skipped)

Note: Security stack {APP_NAMESPACE}-{APP_ENV}-security is preserved.
To remove security infrastructure, use /ipa.security.

Note: Prepare stacks (scripts/prepare.mk) are preserved.
To remove prepare infrastructure: make -f scripts/prepare.mk teardown-prepare

Re-run /ipa.destroy at any time — it is safe to re-run (idempotent).
```

---

## Failure Handling

### Teardown-Specific Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot delete export {name}` | Another stack imports an output from this stack (cross-stack reference) | Delete the dependent stack first. Teardown targets in `deploy.mk` are ordered to prevent this — check for manually-created stacks outside IPA that may reference this stack's exports |
| `The bucket you tried to delete is not empty` | S3 bucket contains objects | Empty the bucket first: `aws s3 rm s3://{bucket-name} --recursive --profile {AWS_PROFILE}`, then re-run `/ipa.destroy` |
| `RepositoryNotEmptyException` or `Repository not empty` | ECR repository contains images | Delete all images first: `aws ecr batch-delete-image --repository-name {repo} --image-ids "$(aws ecr list-images --repository-name {repo} --query 'imageIds[*]' --output json)" --profile {AWS_PROFILE}`, then re-run `/ipa.destroy` |
| Partial teardown (some stacks deleted, others remain) | A stack in the middle of the reverse-order sequence failed to delete | Fix the failing stack (see specific errors above), then re-run `/ipa.destroy`. Already-deleted stacks will be skipped (they no longer exist) |
| `Stack [{stack}] does not exist` during teardown | Stack was already deleted (manually or in a previous attempt) | This is safe to ignore. The teardown will continue with remaining stacks |
| `DELETE_FAILED` | A resource within the stack cannot be deleted | Run `uv run --project utils deploy cfn-events --stack-name {stack-name}` to identify the blocking resource. Fix the issue manually (empty the resource, remove dependencies), then re-run `/ipa.destroy` |

### Credential Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ExpiredTokenException` or `ExpiredToken` | AWS session token has expired | Refresh credentials: re-authenticate with your AWS profile, then re-run `/ipa.destroy` |
| `Access Denied` | Insufficient permissions to delete stacks | Run `/ipa.security` to update the builder role's IAM permissions, then re-run `/ipa.destroy` |

### Tool Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `make: command not found` | GNU Make is not installed | macOS: pre-installed. Linux: `sudo apt install make` |
| `uv: command not found` | uv is not installed | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `make: *** No rule to make target 'teardown'` | `scripts/deploy.mk` is missing or malformed | Run `/ipa.compose` to regenerate deployment artifacts |
