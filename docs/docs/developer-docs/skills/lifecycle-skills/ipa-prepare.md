---
title: /ipa.prepare
sidebar_position: 5
---

# /ipa.prepare

Deploy one-time prerequisite infrastructure (ECR repositories, Cognito User Pool) by executing `scripts/prepare.mk`.

## Invocation

    /ipa.prepare

## Parameters

`/ipa.prepare` takes no arguments. It reads configuration from `.env` and executes `scripts/prepare.mk`.

**Prerequisites:**

| Requirement | Source |
|-------------|--------|
| `.env` with IPA variables | `/ipa.init` |
| Security stack deployed | `/ipa.security` |
| `scripts/prepare.mk` | `/ipa.compose` |
| AWS credentials valid | AWS CLI configuration |
| GNU Make installed | System dependency |

## What It Does

1. **Pre-flight validation** — Confirms `.env` exists, required variables are present, `prepare.mk` exists, AWS credentials are valid, and Make is installed.

2. **Display prepare plan** — Runs `make -n -f scripts/prepare.mk prepare` to show the dry-run plan without executing anything.

3. **Confirmation** — Waits for user confirmation before proceeding. When auto-triggered by `/ipa.deploy`, this step is skipped.

4. **Execute** — Runs `make -f scripts/prepare.mk prepare` to deploy prerequisite stacks.

5. **Post-prepare verification** — Confirms all prepare stacks reach a `*_COMPLETE` status via CloudFormation.

6. **Completion report** — Displays stack status and next steps.

## Outputs

| Artifact | Description |
|----------|-------------|
| ECR stack | `{APP_NAMESPACE}-{APP_ENV}-ecr` — Container image repository |
| Cognito stack | `{APP_NAMESPACE}-{APP_ENV}-cognito` — User Pool with OAuth 2.0 |

:::warning
Prepare stacks are not removed by `/ipa.destroy`. To tear them down manually, run:

```
make -f scripts/prepare.mk teardown-prepare
```
:::

## Examples

**Deploy prerequisites before first deployment:**

    /ipa.prepare

Review the dry-run plan and confirm to deploy ECR and Cognito stacks.

## Related Skills

- [/ipa.compose](./ipa-compose.md) — Generates `scripts/prepare.mk`
- [/ipa.deploy](./ipa-deploy.md) — Auto-triggers `/ipa.prepare` if prepare stacks are missing
- [/ipa.destroy](./ipa-destroy.md) — Does not remove prepare stacks
