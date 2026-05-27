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
| BuildImage | String | `aws/codebuild/standard:8.0` | CodeBuild Docker image |
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
| BuildImage | — | `aws/codebuild/standard:8.0` | — (use default) |
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

## Build Environment Requirements

The `aws/codebuild/standard:8.0` image does not include Terraform or `uv`. The buildspec `install` phase installs both: Terraform so that `scripts/env.mk` can read live stack outputs, and `uv` because Python Make targets (`build.mk`, `post-deploy.mk`) invoke `uv run python ...`.

| Requirement | Version | Install Method |
|-------------|---------|----------------|
| Terraform | 1.10.5 | Downloaded from `releases.hashicorp.com` in buildspec install phase |
| uv | latest | `astral.sh/uv/install.sh` in buildspec install phase, copied to `/usr/local/bin/` so it is on PATH for subsequent phases |

The `pre_build` phase asserts both `command -v terraform` and `command -v uv` before invoking env.mk or any consumer Makefile. If a binary is missing, the build fails with an explicit error rather than silently exiting later when a target invokes the tool.

**`uv` PATH note**: the `astral.sh/uv/install.sh` installer drops binaries into `$HOME/.local/bin`, which is not on PATH for non-login shells in CodeBuild. Each subsequent buildspec command runs in a fresh shell, so amending `$HOME/.bashrc` or `.profile` does not propagate. The buildspec copies `uv` and `uvx` into `/usr/local/bin` (which is on PATH for every shell) immediately after install — do not replace this with a PATH-export approach.

### Buildspec YAML Authoring Rules

The buildspec is embedded in the Terraform module as a heredoc string. CodeBuild parses it as YAML at build time. **Avoid bare brace expressions in command lines** — YAML treats `{ ... }` as a flow-mapping literal and will reject the buildspec with `YAML_FILE_ERROR: Expected Commands[N] to be of string type: found subkeys instead`.

Wrong (parses as a mapping, fails at DOWNLOAD_SOURCE):

```yaml
commands:
  - command -v terraform || { echo "ERROR: not found"; exit 1; }
```

Right (block scalar — every shell construct including `{`, `}`, `:`, `&`, `|` is treated as plain text):

```yaml
commands:
  - |
    if ! command -v terraform > /dev/null; then
      echo "ERROR: terraform binary not found"
      exit 1
    fi
```

Rule of thumb: any command containing `{`, `}`, `: ` (colon followed by space), `[`, `]`, `&`, or unquoted `#` must be written as a `- |` block scalar, not an inline `- ...` scalar.

**Compliance check (MUST run before committing template changes):** After editing the buildspec section of `codepipeline.yml`, grep for bare braces in command scalars:

```bash
grep -n '^\s*- .*[{]' infra/cfn/codepipeline/codepipeline.yml
```

If any match is found outside a `- |` block scalar context, rewrite it as a multi-line block scalar before committing.

## Terraform Module

| Property | Value |
|----------|-------|
| Module path | `infra/tf/codepipeline/` |
| State key | `{namespace}-{env}/codepipeline/terraform.tfstate` |
| Required version | `>= 1.5.0` |
| Providers | `hashicorp/aws >= 5.0` |

### Variables

| Variable | Type | Default | Maps to CFN |
|----------|------|---------|-------------|
| namespace | string | — | Namespace |
| environment | string | — | Environment |
| region | string | — | (implicit) |
| state_bucket | string | — | (TF infrastructure) |
| account_id | string | — | AccountId |
| codebuild_role_arn | string | — | CodeBuildRoleArn |
| source_repo_name | string | — | SourceRepoName |
| source_branch | string | `main` | SourceBranch |
| build_image | string | `aws/codebuild/standard:8.0` | BuildImage |
| compute_type | string | `BUILD_GENERAL1_LARGE` | ComputeType |

### Outputs

| Output | Maps to CFN |
|--------|-------------|
| pipeline_name | PipelineName |
| pipeline_arn | PipelineArn |
| codebuild_project_name | CodeBuildProjectName |
| artifacts_bucket | ArtifactsBucket |

### Remote State References

| Source Module | Data Source | Outputs Used |
|--------------|-------------|--------------|
| codecommit | `terraform_remote_state.codecommit` | repository_name |
