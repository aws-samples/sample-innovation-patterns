---
name: ipa.deploy
description: "Deploy composed infrastructure patterns by executing generated Makefiles.
  Use when the user says 'deploy', 'stand up', 'create stacks', or invokes /ipa.deploy.
  For teardown, use /ipa.destroy."
model: opus
---

# /ipa.deploy — Deploy Infrastructure Pattern

This skill executes the deployment of a composed infrastructure pattern by running generated Makefiles. It validates prerequisites, displays a deployment plan, executes the build and deploy phases, verifies stack states, diagnoses failures, and reports results.

**Prerequisite workflow**: `/ipa.init` → `/ipa.security` → `/ipa.compose` → **`/ipa.deploy`**

---

## What This Skill Does

1. Validates prerequisites (.env, Makefiles, AWS credentials, required tools)
2. Displays a deployment plan via `make -n` (Make dry-run)
3. Runs `make -f scripts/build.mk build` (always — Make handles no-op)
4. Runs `make -f scripts/deploy.mk deploy` (deploys all stacks in dependency order)
5. Verifies deployed stacks reach `*_COMPLETE` status
6. Reports results with stack outputs, endpoints, and next steps

## What This Skill Does NOT Do

- Does not read pattern files, stack SKILL.md, or TROUBLESHOOT.md — Makefiles are the only deployment contract
- Does not generate Makefiles — that's `/ipa.compose`'s job
- Does not create IAM roles — that's `/ipa.security`'s job
- Does not tear down infrastructure — use `/ipa.destroy`
- Does not generate CloudFormation templates — templates are either static (`infra/cfn/`) or generated
- Does not call AWS APIs directly — delegates to `make` which calls `uv run --project utils deploy cfn`
- Does not support per-stack targeting — always deploys the full pattern via aggregate targets
- Does not modify `.env` — it is a read-only consumer of configuration

## Information Sources

| Source | What Deploy Reads | When |
|--------|------------------|------|
| `.env` | `APP_NAMESPACE`, `APP_ENV`, `AWS_REGION`, `AWS_PROFILE`, `AWS_ACCOUNT_ID`, `APP_BUILDER_ROLE_ARN` | Pre-flight validation |
| `scripts/deploy.mk` | Target names, deployment order, stack names | Plan display + execution |
| `scripts/build.mk` | Target names (may be no-op) | Build phase (always run — Make handles no-op) |
| `make -n` | Dry-run output showing commands that would execute | Deployment plan display |
| `uv run --project utils deploy cfn-status` | Stack status | Pre-deploy checks + post-execution verification |
| `uv run --project utils deploy cfn-events` | Stack events | Failure diagnosis (primary diagnostic tool) |
| `uv run --project utils deploy cfn-outputs` | Stack outputs | Post-deploy reporting |
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

Check that `scripts/deploy.mk` exists and contains a `deploy` target.

**If missing**: "`scripts/deploy.mk` not found. Run `/ipa.compose` to generate deployment artifacts."

### 1.4 Verify Build Script Exists

Check that `scripts/build.mk` exists.

**If missing**: "`scripts/build.mk` not found. Run `/ipa.compose` to generate build artifacts."

### 1.5 Verify Security Stack Is Deployed

Run:

```bash
uv run --project utils deploy cfn-status --stack-name {APP_NAMESPACE}-{APP_ENV}-security
```

Expected: `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

**If not deployed**: "Security stack `{APP_NAMESPACE}-{APP_ENV}-security` is not deployed. Run `/ipa.security` first."

### 1.6 Verify AWS Credentials

Run:

```bash
aws sts get-caller-identity --profile {AWS_PROFILE} --region {AWS_REGION}
```

**If fails**: "AWS credentials are invalid or expired for profile `{AWS_PROFILE}`. Refresh your credentials and try again."

### 1.7 Verify Make Is Installed

Run `which make`.

**If missing**: "GNU Make is not installed. On macOS it is pre-installed. On Linux: `sudo apt install make`."

### 1.8 Verify uv Is Installed

Run `which uv`.

**If missing**: "`uv` is not installed. Install via: `curl -LsSf https://astral.sh/uv/install.sh | sh`"

### Validation Summary

If **any** checks fail, display all failures in a single summary table and **STOP**:

```
Pre-flight validation failed:

  ✗ .env variable APP_BUILDER_ROLE_ARN missing — Run /ipa.security
  ✗ AWS credentials expired — Refresh credentials for profile {AWS_PROFILE}

Fix the above issues and re-run /ipa.deploy.
```

If **all** checks pass: "Pre-flight validation passed. All prerequisites verified."

---

## Step 2: Display Deployment Plan + Confirmation

Run Make dry-run to show exactly what will execute:

```bash
make -n -f scripts/deploy.mk deploy
```

Parse the output and display a human-readable deployment plan:

```
Deployment Plan: {APP_NAMESPACE}-{APP_ENV}

  Stack                              Action
  ─────────────────────────────────  ──────
  {APP_NAMESPACE}-{APP_ENV}-ecr      create/update
  {APP_NAMESPACE}-{APP_ENV}-cognito  create/update
  {APP_NAMESPACE}-{APP_ENV}-lambda   create/update (depends on: ecr, cognito)

Proceed with deployment? (yes/no):
```

- **If confirmed**: proceed to Step 3.
- **If declined**: "Deployment cancelled. No changes were made."

---

## Step 3: Execute Build Phase

Run:

```bash
make -f scripts/build.mk build
```

Always execute this step — Make handles no-ops. If `build.mk` has no real targets, the aggregate target outputs "No build targets for this pattern" and exits 0.

Display Make output as it runs.

**If build fails** (exit code ≠ 0): Display the full Make output, propose a fix based on the error, and **STOP**. Do not proceed to deploy.

---

## Step 4: Execute Deploy

Run:

```bash
make -f scripts/deploy.mk deploy
```

Display Make output as it runs. Each target prints its `uv run` command, providing natural progress indication.

**If deploy succeeds** (exit code = 0): proceed to Step 5.

**If deploy fails** (exit code ≠ 0): go to [Failure Diagnosis](#failure-diagnosis).

**Idempotency**: Re-running deploy after a partial failure is always safe. The execution layer handles all state transitions:
- Non-existent stack → `CreateStack`
- `ROLLBACK_COMPLETE` → delete, then recreate
- `*_COMPLETE` → `UpdateStack`
- No changes → succeeds silently ("No updates are to be performed")

---

## Step 5: Post-Deploy Verification

For each stack deployed by `scripts/deploy.mk`, run:

```bash
uv run --project utils deploy cfn-status --stack-name {stack-name}
```

Confirm all stacks report `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

Then collect outputs for reporting:

```bash
uv run --project utils deploy cfn-outputs --stack-name {stack-name}
```

Optionally, run an overview of all managed stacks:

```bash
uv run --project utils deploy cfn-list --namespace {APP_NAMESPACE} --env {APP_ENV}
```

---

## Step 6: Completion Report

Display a structured report:

```
Deployment Complete: {APP_NAMESPACE}-{APP_ENV}

  Stack                              Status
  ─────────────────────────────────  ───────────────
  {APP_NAMESPACE}-{APP_ENV}-ecr      CREATE_COMPLETE
  {APP_NAMESPACE}-{APP_ENV}-cognito  CREATE_COMPLETE
  {APP_NAMESPACE}-{APP_ENV}-lambda   CREATE_COMPLETE

  Outputs:
  ────────
  {APP_NAMESPACE}-{APP_ENV}-ecr:
    RepositoryUri = 123456789012.dkr.ecr.us-east-1.amazonaws.com/ipatest-dev-ecr

Next steps:
  • Review deployed resources in the AWS Console
  • Run /ipa.codepipeline to set up CI/CD (optional)
  • Run /ipa.destroy to tear down infrastructure when no longer needed
  • Re-run /ipa.deploy at any time — it is safe to re-run (idempotent)
```

---

## Failure Diagnosis

When a Make target fails during deployment (Step 4), follow this procedure to diagnose and recover.

### 1. Detect the Failed Stack

Read the Make output to identify which target failed. The failed stack name follows the `--stack-name` flag in the `uv run` command that errored.

### 2. Read Stack Events

```bash
uv run --project utils deploy cfn-events --stack-name {failed-stack-name}
```

This returns recent events in chronological order with resource status and status reason.

### 3. Classify the Error

Match event text against the error classification table in [DIAGNOSIS.md](DIAGNOSIS.md). The five categories are:

| Category | Recovery |
|----------|----------|
| Permission denied | **Manual** — advise re-running `/ipa.security` |
| Validation error | **Manual** — show error, advise checking template/params |
| Resource conflict | **Manual** — advise changing `APP_NAMESPACE` or manual delete |
| Stuck rollback | **Auto** — offer to delete stack + retry |
| Transient/throttle | **Auto** — offer to wait + retry |

### 4. Execute Recovery

**For simple recoveries** (stuck rollback, transient — marked Auto):

1. Explain the diagnosis and proposed fix to the builder.
2. Ask: "Would you like me to fix this automatically? (yes/no):"
3. If confirmed, execute the fix:
   - **Stuck rollback**: `uv run --project utils deploy cfn-delete --stack-name {failed-stack}`, wait for deletion, then re-run `make -f scripts/deploy.mk deploy`.
   - **Transient**: Wait 30 seconds, then re-run `make -f scripts/deploy.mk deploy`.

**For complex fixes** (permission, validation, resource conflict — marked Manual):

1. Explain the diagnosis and the specific error from `cfn-events`.
2. Advise the builder on what to do — see [DIAGNOSIS.md](DIAGNOSIS.md) for per-category guidance.
3. After the builder has applied the fix, they should re-run `/ipa.deploy`.

For deploy-level failures not covered by CloudFormation events (Make errors, tool missing, credential issues), see [TROUBLESHOOT.md](TROUBLESHOOT.md).

---

## Error Handling

### No-Op Build

If `scripts/build.mk` has no real targets, the `build` aggregate target outputs "No build targets for this pattern" and exits 0. This is expected — proceed to deployment.

### Dependent Stack Failure

If a stack fails but its prerequisites succeeded, Make stops at the failed target. Already-deployed prerequisite stacks remain untouched. Re-running deploy after fixing the root cause will skip completed stacks and retry only the failed one.

### Credential Expiry Mid-Deployment

If credentials expire during a long-running deployment (e.g., temporary STS tokens with short TTL), the current `uv run` command will fail with an access denied error. The builder should refresh credentials and re-run `/ipa.deploy` — idempotency ensures already-deployed stacks are not affected.

### Deployment Timeout

CloudFormation deployments have a 60-minute default timeout. If a stack exceeds this, `cfn-events` will show the timeout. Advise the builder to check the stack status in the AWS Console — the stack may still be in progress.

### Network Connectivity Loss

If connectivity is lost mid-deployment, the current command will fail. Advise the builder that infrastructure may be in a transitional state. They should:

1. Check stack status: `uv run --project utils deploy cfn-list --namespace {APP_NAMESPACE} --env {APP_ENV}`
2. Wait for any `IN_PROGRESS` stacks to reach a terminal state.
3. Re-run `/ipa.deploy` to complete the deployment.
