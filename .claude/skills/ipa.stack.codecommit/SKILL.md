---
name: ipa-stack-codecommit
description: "Deploy a CodeCommit repository for source code management."
---

# ipa.stack.codecommit

Deploy a CodeCommit source code repository. Provides repository name, ARN, and clone URL outputs for the codepipeline stack and builder instructions.

## CloudFormation Contract

- **Template**: `infra/cfn/codecommit/codecommit.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-codecommit`
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter" |
| RepositoryName | String | — | `/^[a-zA-Z0-9._-]+$/` | "Only alphanumeric characters, dots, underscores, and hyphens allowed" |
| RepositoryDescription | String | `IPA-managed source repository` | — | — |
| KmsKeyArn | String | *(empty)* | `/^(arn:aws:kms:[a-z0-9-]+:\d{12}:key\/[a-f0-9-]+)?$/` | "Invalid KMS key ARN format" |

All parameters are **Configuration** type — sourced from `.env`, builder input, or defaults.

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| RepositoryName | CodeCommit repository name | `{StackName}-RepositoryName` | ipa.stack.codepipeline (SourceRepoName parameter) |
| RepositoryArn | CodeCommit repository ARN | `{StackName}-RepositoryArn` | Security policy scoping |
| CloneUrlHttp | HTTPS clone URL for the repository | `{StackName}-CloneUrlHttp` | Builder (git remote add) |

## Security Summary

**Required IAM actions**: codecommit:CreateRepository, DeleteRepository, GetRepository, UpdateRepositoryDescription, TagResource, UntagResource — scoped to `arn:aws:codecommit:{Region}:{AccountId}:{RepositoryName}`. Optional KMS actions when `KmsKeyArn` is provided.
**Security controls**: Optional KMS encryption at rest, no public access (CodeCommit is private by default)
**Full advisory**: See [SECURITY.md](SECURITY.md)
