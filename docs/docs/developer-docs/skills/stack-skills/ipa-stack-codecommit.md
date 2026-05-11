---
title: /ipa-stack-codecommit
sidebar_position: 3
---

# /ipa-stack-codecommit

CodeCommit repository for source code management. Managed by `/ipa-codepipeline`, not by `/ipa-compose`.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-codecommit` |
| Template | `infra/cfn/codecommit/codecommit.yml` |
| Capabilities | None |
| Lifecycle | infrastructure |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RepositoryName` | *(prompted by `/ipa-codepipeline`)* | CodeCommit repository name. Alphanumeric characters, dots, underscores, and hyphens. |
| `RepositoryDescription` | `IPA-managed source repository` | Repository description |
| `KmsKeyArn` | *(none)* | Optional KMS key ARN for encryption |

## Outputs

| Output | Description |
|--------|-------------|
| `RepositoryName` | CodeCommit repository name |
| `RepositoryArn` | Repository ARN |
| `CloneUrlHttp` | HTTPS clone URL for git operations |

## Related Skills

- [/ipa-codepipeline](../lifecycle-skills/ipa-codepipeline.md) — Creates and manages this stack
- [/ipa-stack-codepipeline](./ipa-stack-codepipeline.md) — Pipeline stack that reads from this repository
