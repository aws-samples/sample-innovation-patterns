---
title: Installation
sidebar_position: 2
---

# Installation

## Compose

The CodePipeline stack is a composable prepare-lifecycle stack integrated into `/ipa-compose`. To add it to the composition:

    /ipa-compose codepipeline

The compose skill auto-includes `codecommit` as a transitive dependency and prompts for the CodeCommit repository name and branch. The generated `prepare.mk` includes `prepare-codecommit` and `prepare-codepipeline` targets with all cross-stack wiring.

To deploy the stacks:

    /ipa-prepare

## Configuration

### Project Parameters (from `.env`)

| Parameter | Type | Description |
|-----------|------|-------------|
| `Namespace` | String | Project namespace prefix for resource naming. |
| `Environment` | String | Deployment environment (e.g., `dev`, `staging`, `prod`). |
| `AccountId` | String | 12-digit AWS account ID. Must match the pattern `\d{12}`. |

### Cross-Stack Parameters (wired automatically)

| Parameter | Type | Source | Description |
|-----------|------|--------|-------------|
| `CodeBuildRoleArn` | String | `/ipa-security` | CodeBuild execution role ARN provisioned by the security stack. |
| `EcrRepoUri` | String | ECR stack `RepositoryUri` | Full ECR repository URI for container image references. |
| `OidcIssuer` | String | Cognito stack `IssuerUrl` | Cognito OIDC issuer URL for JWT validation. |
| `OidcClientId` | String | Cognito stack `UserPoolClientId` | Cognito app client ID for OIDC audience. |
| `OidcEndSessionEndpoint` | String | Cognito stack `EndSessionEndpoint` | Cognito end-session endpoint URL. |

### Source Parameters (builder input)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `SourceRepoName` | String | -- | CodeCommit repository name. Must match an existing repository. |
| `SourceBranch` | String | `main` | Branch to monitor for pipeline triggers. |

### Build Parameters (optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `BuildImage` | String | `aws/codebuild/standard:7.0` | CodeBuild Docker image for the build environment. |
| `ComputeType` | String | `BUILD_GENERAL1_LARGE` | CodeBuild compute type. Allowed values: `BUILD_GENERAL1_SMALL`, `BUILD_GENERAL1_MEDIUM`, `BUILD_GENERAL1_LARGE`. |
| `KmsKeyArn` | String | *(empty)* | Optional KMS key ARN for artifact encryption at rest. When empty, the artifact bucket uses SSE-S3 (AES256). |

## Wiring

The CodePipeline stack receives values from multiple upstream stacks. The `/ipa-compose` skill wires these references automatically in the generated `prepare.mk`.

| CodePipeline Parameter | Source Stack | Source Output | Notes |
|------------------------|-------------|---------------|-------|
| `CodeBuildRoleArn` | Security | `APP_CODEBUILD_ROLE_ARN` | Stored in `.env` by `/ipa-security` |
| `EcrRepoUri` | ECR | `RepositoryUri` | Full ECR URI without tag |
| `OidcIssuer` | Cognito | `IssuerUrl` | OIDC issuer endpoint |
| `OidcClientId` | Cognito | `UserPoolClientId` | OIDC client ID |
| `OidcEndSessionEndpoint` | Cognito | `EndSessionEndpoint` | End-session endpoint URL |
| `SourceRepoName` | CodeCommit | `RepositoryName` | Repository must exist before pipeline creation |

## Outputs

| Output | Description | Export Name |
|--------|-------------|-------------|
| `PipelineName` | CodePipeline pipeline name | `{StackName}-PipelineName` |
| `PipelineArn` | CodePipeline pipeline ARN | `{StackName}-PipelineArn` |
| `CodeBuildProjectName` | CodeBuild project name | `{StackName}-CodeBuildProjectName` |
| `ArtifactBucketName` | S3 bucket name for pipeline artifacts | `{StackName}-ArtifactBucketName` |
