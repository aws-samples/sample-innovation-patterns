---
title: /ipa.security
sidebar_position: 3
---

# /ipa.security

Provision centralized IAM execution roles and an S3 log bucket for an IPA project. This is the second skill in the IPA workflow, invoked after `/ipa.init`.

## Invocation

    /ipa.security

## Parameters

`/ipa.security` reads prerequisites from `.env` and prompts for the configuration path interactively.

| Parameter | Description |
|-----------|-------------|
| Configuration path | **Managed Policy** (IPA creates roles) or **Existing Role ARNs** (user provides pre-provisioned ARNs) |

**Prerequisites from `.env`:**

| Variable | Source |
|----------|--------|
| `AWS_REGION` | `/ipa.init` |
| `AWS_ACCOUNT_ID` | `/ipa.init` |
| `APP_NAMESPACE` | `/ipa.init` |
| `APP_ENV` | `/ipa.init` |

## What It Does

1. **Validates prerequisites** — Confirms `.env` exists and contains all required variables from `/ipa.init`.

2. **Prompts for configuration path:**
   - **Path 1 — Managed Policy:** IPA generates a CloudFormation template that creates a Builder role and a CodeBuild role with an attached managed policy.
   - **Path 2 — Existing Role ARNs:** The user provides pre-provisioned role ARNs and IPA stores them in `.env`.

3. **Deploys the security stack** — Creates CloudFormation stack `{namespace}-{env}-security` containing IAM roles and an S3 log bucket with SSE-S3 (AES-256) encryption.

4. **Writes security variables to `.env`:**
   - `APP_BUILDER_ROLE_ARN` — Builder execution role ARN
   - `APP_CODEBUILD_ROLE_ARN` — CodeBuild execution role ARN

5. **Handles re-runs** — Detects an existing security stack and offers to update it. Warns before switching configuration paths.

## Outputs

| Artifact | Description |
|----------|-------------|
| CloudFormation stack | `{APP_NAMESPACE}-{APP_ENV}-security` |
| S3 log bucket | `{namespace}-{env}-logs-{account-id}-{region}` |
| `.env` variables | `APP_BUILDER_ROLE_ARN`, `APP_CODEBUILD_ROLE_ARN` |

## Examples

**Provision with IPA-managed roles:**

    /ipa.security

Select "Managed Policy" when prompted. The skill creates IAM roles and writes their ARNs to `.env`.

**Use existing role ARNs:**

    /ipa.security

Select "Existing Role ARNs" and provide the Builder and CodeBuild role ARNs when prompted.

## Related Skills

- [/ipa.init](./ipa-init.md) — Must run first to create `.env` with required variables
- [/ipa.compose](./ipa-compose.md) — Next step after security provisioning
