---
title: /ipa-stack-codecommit
sidebar_position: 3
---

# /ipa-stack-codecommit

CodeCommit repository for source code management. Composed via `/ipa-compose codepipeline` as a prepare-lifecycle stack (auto-included as a transitive dependency of codepipeline).

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-codecommit` |
| Template | `infra/cfn/codecommit/codecommit.yml` |
| Capabilities | None |
| Lifecycle | prepare (prerequisite stack) |
| Tier | codecommit |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RepositoryName` | *(prompted during `/ipa-compose`)* | CodeCommit repository name. Alphanumeric characters, dots, underscores, and hyphens. |
| `RepositoryDescription` | `IPA-managed source repository` | Repository description |
| `KmsKeyArn` | *(none)* | Optional KMS key ARN for encryption |

## Outputs

| Output | Description |
|--------|-------------|
| `RepositoryName` | CodeCommit repository name |
| `RepositoryArn` | Repository ARN |
| `CloneUrlHttp` | HTTPS clone URL for git operations |

## Related Skills

- [/ipa-compose](../lifecycle-skills/ipa-compose.md) — Composes this stack into the project
- [/ipa-prepare](../lifecycle-skills/ipa-prepare.md) — Deploys this stack
- [/ipa-stack-codepipeline](./ipa-stack-codepipeline.md) — Pipeline stack that reads from this repository
