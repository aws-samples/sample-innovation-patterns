---
name: ipa-stack-codepipeline
description: "Deploy a CodePipeline CI/CD pipeline with CodeBuild for automated build/test/deploy."
---

# ipa.stack.codepipeline

Deploy a CI/CD pipeline that runs the same `scripts/*.mk` Makefiles the builder runs locally. Contains CodeBuild project, CodePipeline, artifacts bucket, EventBridge trigger rule, and scoped IAM roles.

## CloudFormation Contract

- **Template**: `infra/cfn/codepipeline/codepipeline.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-codepipeline`
- **Capabilities**: `CAPABILITY_NAMED_IAM`

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

### Wirable Parameters (from other stacks)

| Parameter | Source Stack | Source Output | Description |
|-----------|-------------|---------------|-------------|
| CodeBuildRoleArn | `{ns}-{env}-security` | `CodeBuildRoleArn` | CodeBuild execution role from `/ipa.security` |
| EcrRepoUri | `{ns}-{env}-ecr` | `RepositoryUri` | ECR repository URI |
| OidcIssuer | `{ns}-{env}-cognito` | `IssuerUrl` | Cognito OIDC issuer URL |
| OidcClientId | `{ns}-{env}-cognito` | `UserPoolClientId` | Cognito app client ID |
| OidcEndSessionEndpoint | `{ns}-{env}-cognito` | `EndSessionEndpoint` | Cognito end session endpoint |

## CodeBuild Environment Variables

Set on the CodeBuild project, inherited by Make targets at runtime:

| Variable | Source |
|----------|--------|
| `APP_NAMESPACE` | Parameter `Namespace` |
| `APP_ENV` | Parameter `Environment` |
| `AWS_ACCOUNT_ID` | Parameter `AccountId` |
| `ECR_REPO_URI` | Parameter `EcrRepoUri` |
| `OIDC_ISSUER` | Parameter `OidcIssuer` |
| `OIDC_CLIENT_ID` | Parameter `OidcClientId` |
| `OIDC_END_SESSION_ENDPOINT` | Parameter `OidcEndSessionEndpoint` |
| `IPA_MAKEFILE` | Pipeline action override (default: `build.mk`) |
| `IPA_TARGET` | Pipeline action override (default: `build`) |

Each pipeline stage overrides `IPA_MAKEFILE` and `IPA_TARGET` to select which Make target to run. The buildspec is inline in the template.

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
