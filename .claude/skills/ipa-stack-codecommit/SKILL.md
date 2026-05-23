---
name: ipa-stack-codecommit
description: "Deploy a CodeCommit repository for source code management."
---

# ipa-stack-codecommit

Deploy a CodeCommit source code repository. Provides repository name, ARN, and clone URL outputs for the codepipeline stack and builder instructions.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-codecommit` |
| Template | `infra/cfn/codecommit/codecommit.yml` |
| Capabilities | none |
| Lifecycle | prepare (prerequisite stack) |
| Tier | codecommit |

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter" |
| RepositoryName | String | — | `/^[a-zA-Z0-9._-]+$/` | "Only alphanumeric characters, dots, underscores, and hyphens allowed" |
| RepositoryDescription | String | `IPA-managed source repository` | — | — |
| KmsKeyArn | String | *(empty)* | `/^(arn:aws:kms:[a-z0-9-]+:\d{12}:key\/[a-f0-9-]+)?$/` | "Invalid KMS key ARN format" |

All parameters are **Configuration** type — sourced from `.env`, builder input, or defaults.

## Wirable Parameters

No wirable parameters — all parameters are configuration type (sourced from `.env` or builder input).

## Compose Config

Parameters prompted during `/ipa-compose`:

| Parameter | Prompt | Default | Validation |
|-----------|--------|---------|------------|
| RepositoryName | "CodeCommit repository name?" | `{APP_NAMESPACE}-{APP_ENV}-repo` | `/^[a-zA-Z0-9._-]+$/` |
| RepositoryDescription | — | `IPA-managed source repository` | — (use default) |

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| RepositoryName | CodeCommit repository name | `{StackName}-RepositoryName` | ipa-stack-codepipeline (SourceRepoName parameter) |
| RepositoryArn | CodeCommit repository ARN | `{StackName}-RepositoryArn` | Security policy scoping |
| CloneUrlHttp | HTTPS clone URL for the repository | `{StackName}-CloneUrlHttp` | Builder (git remote add) |

## Security Summary

**Required IAM actions**: codecommit:CreateRepository, DeleteRepository, GetRepository, UpdateRepositoryDescription, TagResource, UntagResource — scoped to `arn:aws:codecommit:{Region}:{AccountId}:{RepositoryName}`. Optional KMS actions when `KmsKeyArn` is provided.
**Security controls**: Optional KMS encryption at rest, no public access (CodeCommit is private by default)
**Full advisory**: See [SECURITY.md](SECURITY.md)

## Terraform Module

| Property | Value |
|----------|-------|
| Module path | `infra/tf/codecommit/` |
| State key | `{namespace}-{env}/codecommit/terraform.tfstate` |
| Required version | `>= 1.5.0` |
| Providers | `hashicorp/aws >= 5.0` |

### Variables

| Variable | Type | Default | Maps to CFN |
|----------|------|---------|-------------|
| namespace | string | — | Namespace |
| environment | string | — | Environment |
| region | string | — | (implicit) |
| state_bucket | string | — | (TF infrastructure) |
| repository_name | string | — | RepositoryName |
| repository_description | string | `IPA-managed source repository` | RepositoryDescription |

### Outputs

| Output | Maps to CFN |
|--------|-------------|
| repository_name | RepositoryName |
| repository_arn | RepositoryArn |
| clone_url_http | CloneUrlHttp |
