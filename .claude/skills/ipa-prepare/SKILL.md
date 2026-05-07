---
name: ipa-prepare
description: "Deploy one-time prerequisite infrastructure from scripts/prepare.mk.
  Use when the user says 'prepare', 'deploy prerequisites', 'create ECR',
  or invokes /ipa-prepare."
model: opus
---

# /ipa-prepare — Deploy Prepare Infrastructure

This skill deploys one-time prerequisite infrastructure by executing
`scripts/prepare.mk`. Prepare stacks (ECR repositories, etc.) must exist
before build and deploy scripts can run.

**Prerequisite workflow**: `/ipa-init` → `/ipa-security` → `/ipa-compose` → **`/ipa-prepare`** → `/ipa-deploy`

---

## What This Skill Does

1. Validates prerequisites (.env, prepare.mk exist, AWS credentials)
2. Displays prepare plan via `make -n -f scripts/prepare.mk prepare`
3. Confirms with builder
4. Runs `make -f scripts/prepare.mk prepare`
5. Verifies all prepare stacks reach `*_COMPLETE` status
6. Writes OIDC configuration to `.env` (if Cognito is a prepare stack)
7. Reports results

## What This Skill Does NOT Do

- Does not generate prepare.mk — that's `/ipa-compose`'s job
- Does not create IAM roles — that's `/ipa-security`'s job
- Does not run build or deploy — use `/ipa-deploy`
- Does not support per-stack targeting — always runs the aggregate `prepare` target

## Invocation Modes

This skill supports two invocation modes:

### Manual Invocation (builder runs `/ipa-prepare`)
Full flow: pre-flight → plan display → confirmation → execute → verify → report.

### Auto-Triggered Invocation (called by `/ipa-deploy`)
Abbreviated flow: **skip pre-flight** → plan display → **skip confirmation** → execute → verify → report.
When invoked from `/ipa-deploy`'s Step 1.3a, the builder has already validated
credentials and `.env` in deploy's own pre-flight. Repeating those checks is redundant.
Skip all of Step 1 (pre-flight validation) and proceed directly to Step 2 (plan display)
with skip-confirmation.

The invocation mode is determined by context: if `/ipa-prepare` is running because
`/ipa-deploy` detected undeployed prepare stacks, it is auto-triggered.

## When to Run

- After first `/ipa-compose` on a new project
- After re-running `/ipa-compose` that adds new prepare stacks
- NOT part of CI/CD — pipeline assumes prepare has already been run

## Information Sources

| Source | What Prepare Reads | When |
|--------|-------------------|------|
| `.env` | `APP_NAMESPACE`, `APP_ENV`, `AWS_REGION`, `AWS_PROFILE` | Pre-flight validation |
| `scripts/prepare.mk` | Target names, stack names | Plan display + execution |
| `make -n` | Dry-run output | Plan display |
| `source .env 2>/dev/null; aws cloudformation describe-stacks` | Stack status | Post-execution verification |

---

## Step 1: Pre-Flight Validation

> **AWS credential resolution**: All `aws` CLI commands must be prefixed with `source .env 2>/dev/null;` to load credentials. Do NOT pass `--profile` or `--region` explicitly.

Run all checks and report all failures at once.

### 1.1 Verify .env Exists

Check `.env` exists at project root and is non-empty.

**If missing**: "`.env` not found. Run `/ipa-init` to initialize project configuration."

### 1.2 Verify Required .env Variables

| Variable | Written By | Error If Missing |
|----------|------------|-----------------|
| `APP_NAMESPACE` | `/ipa-init` | "Missing `APP_NAMESPACE`. Run `/ipa-init`." |
| `APP_ENV` | `/ipa-init` | "Missing `APP_ENV`. Run `/ipa-init`." |
| `AWS_REGION` | `/ipa-init` | "Missing `AWS_REGION`. Run `/ipa-init`." |
| `AWS_PROFILE` | `/ipa-init` | "Missing `AWS_PROFILE`. Run `/ipa-init`." |

### 1.3 Verify prepare.mk Exists

Check `scripts/prepare.mk` exists and contains a `prepare` target.

**If missing**: "`scripts/prepare.mk` not found. Run `/ipa-compose` to generate prepare artifacts."

**If empty/no target**: "`scripts/prepare.mk` has no `prepare` target. Run `/ipa-compose` with a pattern that has prepare stacks."

### 1.4 Verify AWS Credentials

Run: `source .env 2>/dev/null; aws sts get-caller-identity`

**If fails**: "AWS credentials are invalid or expired for profile `{AWS_PROFILE}`."

### 1.5 Verify Make Is Installed

Check `which make`.

### Validation Summary

If any fail, display all failures and STOP. If all pass: "Pre-flight validation passed."

---

## Step 2: Display Prepare Plan + Conditional Confirmation

Run: `make -n -f scripts/prepare.mk prepare`

Display:

```
Prepare Plan: {APP_NAMESPACE}-{APP_ENV}

  Stack                              Action
  ---------------------------------  ------
  {APP_NAMESPACE}-{APP_ENV}-cognito  create/update
  .env                               write OIDC configuration
  {APP_NAMESPACE}-{APP_ENV}-ecr      create/update

These are one-time prerequisite stacks. They must exist before
build and deploy can run.
```

**If manually invoked** (builder ran `/ipa-prepare`):
  Ask: "Proceed? (yes/no):"
  If declined: "Prepare cancelled. No changes were made."

**If auto-triggered** (invoked by `/ipa-deploy` Step 1.3a):
  Display: "Auto-preparing prerequisite stacks..."
  Proceed directly to Step 3 (Execute). Do NOT ask for confirmation.

---

## Step 3: Execute Prepare

Run: `make -f scripts/prepare.mk prepare`

Display Make output as it runs.

**If fails**: Read stack events via `source .env 2>/dev/null; aws cloudformation describe-stack-events --stack-name {failed-stack}`, diagnose, and propose fix. Same error classification as `/ipa-deploy`.

---

## Step 4: Post-Prepare Verification

For each prepare stack, run:

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks --stack-name {stack-name} --query 'Stacks[0].StackStatus' --output text
```

Confirm all report `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

---

## Step 5: Completion Report

```
Prepare Complete: {APP_NAMESPACE}-{APP_ENV}

  Stack                              Status
  ---------------------------------  ---------------
  {APP_NAMESPACE}-{APP_ENV}-cognito  CREATE_COMPLETE
  {APP_NAMESPACE}-{APP_ENV}-ecr      CREATE_COMPLETE
  .env                               OIDC vars written

Next steps:
  - Run `/ipa-deploy` to build and deploy the application
  - Re-run `/ipa-prepare` if prepare stacks change
  - Prepare stacks are NOT auto-deleted by /ipa-destroy — manual teardown:
    make -f scripts/prepare.mk teardown-prepare
```
