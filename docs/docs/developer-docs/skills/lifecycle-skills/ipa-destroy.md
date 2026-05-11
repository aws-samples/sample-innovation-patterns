---
title: /ipa-destroy
sidebar_position: 6
---

# /ipa-destroy

Tear down a deployed infrastructure pattern by executing teardown targets in the generated Makefiles. Removes solution-tier stacks while preserving security and prepare infrastructure.

## Invocation

    /ipa-destroy

## Parameters

`/ipa-destroy` takes no arguments. It reads configuration from `.env` and executes teardown targets in `scripts/deploy.mk`.

**Prerequisites:**

| Requirement | Source |
|-------------|--------|
| `.env` with IPA variables | `/ipa-init` |
| `scripts/deploy.mk` | `/ipa-compose` |
| Security stack deployed | `/ipa-compose` (security phase) |
| AWS credentials valid | AWS CLI configuration |
| GNU Make installed | System dependency |

## What It Does

1. **Pre-flight validation** — Confirms `.env` exists, required variables are present, Makefiles exist, security stack is deployed, AWS credentials are valid, and Make is installed.

2. **Pre-teardown status check** — Extracts stack names from `deploy.mk` and checks each stack's current status (Exists, Gone, Transitioning, or Failed).

3. **Display teardown plan** — Shows the status-aware teardown plan with data loss warnings and dry-run commands.

4. **Double confirmation** — First prompt: "Are you sure?" Second prompt: type the namespace to confirm.

5. **Execute teardown** — Runs `make -f scripts/deploy.mk teardown` to delete stacks in reverse dependency order.

6. **Post-teardown verification** — Confirms all pattern stacks have been deleted.

7. **Completion report** — Shows deletion status and lists preserved infrastructure.

### What Is Preserved

| Infrastructure | Reason |
|---------------|--------|
| Security stack | Managed by `/ipa-security`, not the deployment pattern |
| Prepare stacks (ECR, Cognito) | One-time prerequisites with persistent data |

To tear down prepare stacks manually:

```
make -f scripts/prepare.mk teardown-prepare
```

### Failure Handling

| Failure | Resolution |
|---------|------------|
| Non-empty S3 bucket | Empty the bucket first, then re-run |
| Non-empty ECR repository | Delete all images first, then re-run |
| Cannot delete export | Delete the dependent stack first |
| `DELETE_FAILED` | Identify the blocking resource, fix manually, re-run |

## Outputs

No artifacts are created. Pattern stacks are deleted from CloudFormation.

## Examples

**Tear down a deployed pattern:**

    /ipa-destroy

Review the status of each stack, confirm twice, and the skill deletes stacks in reverse dependency order.

## Related Skills

- [/ipa-deploy](./ipa-deploy.md) — Deploys the stacks that `/ipa-destroy` removes
- [/ipa-compose](./ipa-compose.md) — Generates the Makefiles with teardown targets
- [/ipa-prepare](./ipa-prepare.md) — Prepare stacks are preserved and require manual teardown
