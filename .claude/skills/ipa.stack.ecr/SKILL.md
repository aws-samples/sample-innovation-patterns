---
name: ipa-stack-ecr
description: "Deploy an ECR repository for container image storage."
---

# ipa.stack.ecr

Deploy an ECR container image repository. Provides repository URI and ARN outputs for downstream Lambda stacks and security policy scoping.

## CloudFormation Contract

- **Template**: `infra/cfn/ecr/ecr.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-ecr`
- **Capabilities**: none

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter" |

All parameters are **Configuration** type — sourced from `.env` or defaults. No wirable parameters from other stacks.

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| RepositoryUri | ECR repository URI for container images | `{StackName}-RepositoryUri` | ipa.stack.lambda-fn (ImageUri), ipa.stack.lambda-fn-stream (ImageUri) |
| RepositoryArn | ECR repository ARN for security policy scoping | `{StackName}-RepositoryArn` | Security policy scoping |

## Security Summary

**Required IAM actions**: ecr:CreateRepository, DeleteRepository, DescribeRepositories, TagResource — scoped to `arn:aws:ecr:{Region}:{AccountId}:repository/*`. ecr:GetAuthorizationToken on `*` (AWS API limitation — this action does not support resource-level permissions)
**Security controls**: Encryption at rest (AES256), no public access, no automatic deletion on stack removal
**Full advisory**: See [SECURITY.md](SECURITY.md)
