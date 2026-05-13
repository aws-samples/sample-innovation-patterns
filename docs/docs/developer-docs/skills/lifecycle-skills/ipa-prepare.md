---
title: /ipa-prepare
sidebar_position: 4
---

# /ipa-prepare

Deploy one-time prerequisite infrastructure by executing `scripts/prepare.mk`. This is the third step in the IPA lifecycle, run after `/ipa-compose` generates the Makefiles. Prerequisite stacks include the centralized log bucket, ECR, and Cognito; if `/ipa-compose codepipeline` was run, CodeCommit and CodePipeline stacks are also deployed.

## Invocation

    /ipa-prepare

## Parameters

`/ipa-prepare` takes no arguments. It reads configuration from `.env` and executes `scripts/prepare.mk`.

**Prerequisites:**

| Requirement | Source |
|-------------|--------|
| `.env` with IPA variables | `/ipa-init` |
| IAM roles provisioned | `/ipa-security` (embedded in first compose) |
| `scripts/prepare.mk` | `/ipa-compose` |
| AWS credentials valid | AWS CLI configuration |
| GNU Make installed | System dependency |

## What It Does

1. **Pre-flight validation** — Confirms `.env` exists, required variables are present, `prepare.mk` exists, AWS credentials are valid, and Make is installed.

2. **Display prepare plan** — Runs `make -n -f scripts/prepare.mk prepare` to show the dry-run plan without executing anything.

3. **Confirmation** — Waits for user confirmation before proceeding.

4. **Execute** — Runs `make -f scripts/prepare.mk prepare` to deploy prerequisite stacks.

5. **Post-prepare verification** — Confirms all prepare stacks reach a `*_COMPLETE` status via CloudFormation.

6. **Completion report** — Displays stack status and next steps.

## Outputs

| Artifact | Description |
|----------|-------------|
| Logs stack | `{APP_NAMESPACE}-{APP_ENV}-logs` — Centralized S3 log bucket for access and flow logs |
| ECR stack | `{APP_NAMESPACE}-{APP_ENV}-ecr` — Container image repository |
| Cognito stack | `{APP_NAMESPACE}-{APP_ENV}-cognito` — User Pool with OAuth 2.0 |
| CodeCommit stack | `{APP_NAMESPACE}-{APP_ENV}-codecommit` — Source repository (when composed with `codepipeline`) |
| CodePipeline stack | `{APP_NAMESPACE}-{APP_ENV}-codepipeline` — 5-stage CI/CD pipeline (when composed with `codepipeline`) |

:::warning
Prepare stacks are not removed by `/ipa-destroy`. To tear them down manually, run:

```
make -f scripts/prepare.mk teardown-prepare
```

To tear down only the CI/CD stacks:

```
make -f scripts/prepare.mk teardown-codepipeline teardown-codecommit
```
:::

## Examples

**Deploy prerequisites before first deployment:**

    /ipa-prepare

Review the dry-run plan and confirm to deploy ECR and Cognito stacks (plus CodeCommit and CodePipeline if composed).

## Related Skills

- [/ipa-compose](./ipa-compose.md) — Generates `scripts/prepare.mk`
- [/ipa-deploy](./ipa-deploy.md) — Requires prepare stacks to be deployed first (hard gate — will not auto-prepare)
- [/ipa-destroy](./ipa-destroy.md) — Does not remove prepare stacks
