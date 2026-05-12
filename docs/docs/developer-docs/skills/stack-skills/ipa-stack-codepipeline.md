---
title: /ipa-stack-codepipeline
sidebar_position: 4
---

# /ipa-stack-codepipeline

CI/CD pipeline with CodeBuild for automated build, test, and deploy. Composed via `/ipa-compose codepipeline` as a prepare-lifecycle stack.

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

| Parameter | Default | Description |
|-----------|---------|-------------|
| `Namespace` | *(from `.env`)* | Project namespace |
| `Environment` | *(from `.env`)* | Environment label |
| `AccountId` | *(from `.env`)* | AWS account ID |
| `SourceBranch` | `main` | Branch that triggers the pipeline |
| `BuildImage` | `aws/codebuild/standard:7.0` | CodeBuild image |
| `ComputeType` | `BUILD_GENERAL1_LARGE` | CodeBuild compute type |
| `KmsKeyArn` | *(none)* | Optional KMS key ARN |

### Wirable Parameters

| Parameter | Source Stack | Source Output | Notes |
|-----------|-------------|---------------|-------|
| `CodeBuildRoleArn` | security | CodeBuildRoleArn | From `/ipa-security` stack |
| `EcrRepoUri` | ecr | RepositoryUri | ECR repository URI |
| `OidcIssuer` | cognito | IssuerUrl | OIDC issuer URL |
| `OidcClientId` | cognito | UserPoolClientId | Cognito app client ID |
| `OidcEndSessionEndpoint` | cognito | EndSessionEndpoint | Cognito end session endpoint |
| `SourceRepoName` | codecommit | RepositoryName | CodeCommit repository name |

### Compose Config

| Parameter | Prompt | Default |
|-----------|--------|---------|
| `SourceBranch` | "Branch to trigger pipeline?" | `main` |
| `BuildImage` | — | `aws/codebuild/standard:7.0` |
| `ComputeType` | — | `BUILD_GENERAL1_LARGE` |

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

- [/ipa-compose](../lifecycle-skills/ipa-compose.md) — Composes this stack into the project
- [/ipa-prepare](../lifecycle-skills/ipa-prepare.md) — Deploys this stack
- [/ipa-stack-codecommit](./ipa-stack-codecommit.md) — Source repository for the pipeline
- [/ipa-security](../lifecycle-skills/ipa-security.md) — Provides the CodeBuild execution role
