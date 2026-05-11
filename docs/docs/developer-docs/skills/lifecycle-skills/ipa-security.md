---
title: /ipa-security
sidebar_position: 7
---

# /ipa-security

Provision centralized IAM execution roles and an S3 log bucket for an IPA project. This skill is embedded in `/ipa-compose` and runs automatically on first compose when `APP_BUILDER_ROLE_ARN` is absent from `.env`. It can also be invoked standalone to right-size IAM permissions or switch configuration paths after initial setup.

## Invocation

    /ipa-security

## Parameters

`/ipa-security` reads prerequisites from `.env` and prompts for the configuration path interactively.

| Parameter | Description |
|-----------|-------------|
| Configuration path | One of three paths — see below |

**Prerequisites from `.env`:**

| Variable | Source |
|----------|--------|
| `AWS_REGION` | `/ipa-init` |
| `AWS_ACCOUNT_ID` | `/ipa-init` |
| `APP_NAMESPACE` | `/ipa-init` |
| `APP_ENV` | `/ipa-init` |

## What It Does

1. **Validates prerequisites** — Confirms `.env` exists and contains all required variables from `/ipa-init`.

2. **Prompts for configuration path:**

   | Path | Name | Description |
   |------|------|-------------|
   | A | **Existing Role ARN** | The user provides pre-provisioned role ARNs and IPA stores them in `.env`. No CloudFormation deployed. |
   | B | **Managed Policy** | IPA generates a CloudFormation template that creates a Builder role and a CodeBuild role with an attached managed policy (`PowerUserAccess`). |
   | C | **Innovation Builder Stack** (recommended) | IPA deploys a purpose-built security stack with scoped IAM roles, a log bucket, and boundary policies. Best balance of speed and least-privilege. |

3. **Deploys the security stack** (Paths B and C) — Creates CloudFormation stack `{namespace}-{env}-security` containing IAM roles and an S3 log bucket with SSE-S3 (AES-256) encryption.

4. **Writes security variables to `.env`:**
   - `APP_BUILDER_ROLE_ARN` — Builder execution role ARN
   - `APP_CODEBUILD_ROLE_ARN` — CodeBuild execution role ARN

5. **Handles re-runs** — Detects an existing security stack and offers to update it. Warns before switching configuration paths.

:::info Embedded in /ipa-compose
In the standard workflow, this skill is triggered automatically by `/ipa-compose` on first compose. You only need to invoke `/ipa-security` directly to right-size IAM after initial setup or to switch between configuration paths.
:::

## Outputs

| Artifact | Description |
|----------|-------------|
| CloudFormation stack | `{APP_NAMESPACE}-{APP_ENV}-security` |
| S3 log bucket | `{namespace}-{env}-logs-{account-id}-{region}` |
| `.env` variables | `APP_BUILDER_ROLE_ARN`, `APP_CODEBUILD_ROLE_ARN` |

## Examples

**Provision with IPA-managed roles:**

    /ipa-security

Select "Managed Policy" when prompted. The skill creates IAM roles and writes their ARNs to `.env`.

**Use existing role ARNs:**

    /ipa-security

Select "Existing Role ARNs" and provide the Builder and CodeBuild role ARNs when prompted.

## Related Skills

- [/ipa-init](./ipa-init.md) — Must run first to create `.env` with required variables
- [/ipa-compose](./ipa-compose.md) — Embeds `/ipa-security` on first compose; next step after security provisioning
