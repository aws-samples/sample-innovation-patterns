---
name: ipa-stack-codepipeline
description: "Deploy a CodePipeline CI/CD pipeline with CodeBuild for automated build/test/deploy."
---

# ipa-stack-codepipeline

Deploy a CI/CD pipeline that runs the same `scripts/*.mk` Makefiles the builder runs locally. Contains CodeBuild project, CodePipeline, artifacts bucket, EventBridge trigger rule, and scoped IAM roles.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-codepipeline` |
| Template | `infra/cfn/codepipeline/codepipeline.yml` |
| Capabilities | `CAPABILITY_NAMED_IAM` |
| Lifecycle | prepare (prerequisite stack) |
| Tier | codepipeline |

## Parameters

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| Namespace | String | — | Project namespace prefix (from `.env` `APP_NAMESPACE`) |
| Environment | String | — | Environment name (from `.env` `APP_ENV`) |
| AccountId | String | — | 12-digit AWS account ID (from `.env` `AWS_ACCOUNT_ID`) |
| SourceRepoName | String | — | CodeCommit repository name (builder input) |
| SourceBranch | String | `main` | Branch to track for pipeline triggers |
| BuildImage | String | `aws/codebuild/standard:7.0` | CodeBuild Docker image |
| ComputeType | String | `BUILD_GENERAL1_LARGE` | CodeBuild compute type |
| KmsKeyArn | String | *(empty)* | Optional KMS key ARN for encryption at rest |

## Wirable Parameters

Parameters that receive values from other stacks during composition:

| Parameter | Source Stack | Source Output | Notes |
|-----------|-------------|---------------|-------|
| CodeBuildRoleArn | security | CodeBuildRoleArn | From `/ipa-security` stack |
| SourceRepoName | codecommit | RepositoryName | CodeCommit repository name |

**ECR and Cognito outputs are NOT pipeline parameters.** Each CodeBuild stage runs `make -f scripts/env.mk update-env` as its prelude, populating `.env` with `ECR_REPO_URI`, `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_END_SESSION_ENDPOINT`, and other live stack outputs. This avoids stale CodeBuild EnvironmentVariables overriding live values via Make's environment-precedence rule.

## Deploy Order

| Constraint | Reason |
|------------|--------|
| codepipeline deploys after codecommit | SourceRepoName wiring dependency |

## Compose Config

Parameters prompted during `/ipa-compose`:

| Parameter | Prompt | Default | Validation |
|-----------|--------|---------|------------|
| SourceBranch | "Branch to trigger pipeline?" | `main` | — |
| BuildImage | — | `aws/codebuild/standard:7.0` | — (use default) |
| ComputeType | — | `BUILD_GENERAL1_LARGE` | — (use default) |

## CodeBuild Environment Variables

Set on the CodeBuild project — **only orchestration/identity values**. Stack outputs are not baked into CodeBuild env vars; they are written to `.env` by `scripts/env.mk` in each stage's prelude.

| Variable | Source |
|----------|--------|
| `APP_NAMESPACE` | Parameter `Namespace` |
| `APP_ENV` | Parameter `Environment` |
| `AWS_ACCOUNT_ID` | Parameter `AccountId` |
| `IPA_MAKEFILE` | Pipeline action override (default: `build.mk`) |
| `IPA_TARGET` | Pipeline action override (default: `build`) |

Each pipeline stage overrides `IPA_MAKEFILE` and `IPA_TARGET` to select which Make target to run. The buildspec is inline in the template; its prelude runs `make -f scripts/env.mk update-env` (when `IPA_MAKEFILE != test.mk`) so consumer Makefiles can read live stack outputs via `-include .env`.

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| PipelineName | Pipeline name | `{StackName}-PipelineName` | Process skill (written to `.env`) |
| PipelineArn | Pipeline ARN | `{StackName}-PipelineArn` | Security policy scoping |
| CodeBuildProjectName | CodeBuild project name | `{StackName}-CodeBuildProjectName` | Process skill (written to `.env`) |
| ArtifactBucketName | Artifact bucket name | `{StackName}-ArtifactBucketName` | Reference |

## Security Summary

**Required IAM actions**: See [SECURITY.md](SECURITY.md) for full deployment permissions.
**Security controls**: No wildcard IAM ARNs (PipelineRole scoped to specific resources), artifact bucket blocks public access + denies non-SSL, SSE-S3 or KMS encryption, CodeBuild uses external execution role.
**Capabilities**: `CAPABILITY_NAMED_IAM` required (creates PipelineRole and EventRuleRole).
**Full advisory**: See [SECURITY.md](SECURITY.md)
