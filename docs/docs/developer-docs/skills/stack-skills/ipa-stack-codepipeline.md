---
title: /ipa-stack-codepipeline
sidebar_position: 4
---

# /ipa-stack-codepipeline

CI/CD pipeline with CodeBuild for automated build, test, and deploy. Managed by `/ipa-codepipeline`, not by `/ipa-compose`.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-codepipeline` |
| Template | `infra/cfn/codepipeline/codepipeline.yml` |
| Capabilities | `CAPABILITY_NAMED_IAM` |
| Lifecycle | infrastructure |

## Parameters

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `Namespace` | *(from `.env`)* | Project namespace |
| `Environment` | *(from `.env`)* | Environment label |
| `AccountId` | *(from `.env`)* | AWS account ID |
| `SourceRepoName` | *(prompted)* | CodeCommit repository name |
| `SourceBranch` | `main` | Branch that triggers the pipeline |
| `BuildImage` | `aws/codebuild/standard:7.0` | CodeBuild image |
| `ComputeType` | `BUILD_GENERAL1_LARGE` | CodeBuild compute type |
| `KmsKeyArn` | *(none)* | Optional KMS key ARN |

### Wirable Parameters

| Parameter | Source |
|-----------|--------|
| `CodeBuildRoleArn` | security.CodeBuildRoleArn |
| `EcrRepoUri` | ecr.RepositoryUri |
| `OidcIssuer` | cognito.IssuerUrl |
| `OidcClientId` | cognito.UserPoolClientId |
| `OidcEndSessionEndpoint` | cognito.EndSessionEndpoint |

### CodeBuild Environment Variables

The pipeline injects these environment variables into CodeBuild, which are inherited by Make targets:

| Variable | Description |
|----------|-------------|
| `APP_NAMESPACE` | Project namespace |
| `APP_ENV` | Environment label |
| `AWS_ACCOUNT_ID` | AWS account ID |
| `ECR_REPO_URI` | ECR repository URI |
| `OIDC_ISSUER` | Cognito OIDC issuer URL |
| `OIDC_CLIENT_ID` | Cognito client ID |
| `OIDC_END_SESSION_ENDPOINT` | Cognito logout URL |
| `IPA_MAKEFILE` | Makefile path (set per pipeline action) |
| `IPA_TARGET` | Make target (set per pipeline action) |

## Pipeline Stages

| Stage | Makefile | Target |
|-------|----------|--------|
| Test | `scripts/test.mk` | `test` |
| Build | `scripts/build.mk` | `build` |
| Deploy | `scripts/deploy.mk` | `deploy` |
| PostDeploy | `scripts/post-deploy.mk` | `post-deploy` |

## Outputs

| Output | Description |
|--------|-------------|
| `PipelineName` | CodePipeline name |
| `PipelineArn` | Pipeline ARN |
| `CodeBuildProjectName` | CodeBuild project name |
| `ArtifactBucketName` | S3 bucket for pipeline artifacts |

## Related Skills

- [/ipa-codepipeline](../lifecycle-skills/ipa-codepipeline.md) — Creates and manages this stack
- [/ipa-stack-codecommit](./ipa-stack-codecommit.md) — Source repository for the pipeline
- [/ipa-security](../lifecycle-skills/ipa-security.md) — Provides the CodeBuild execution role
