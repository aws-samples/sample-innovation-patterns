---
title: /ipa-codepipeline
sidebar_position: 8
---

# /ipa-codepipeline

Deploy a CI/CD pipeline that automates the same build, test, and deploy workflow that runs locally via Makefiles. Creates a CodeCommit repository and a CodePipeline with CodeBuild.

## Invocation

    /ipa-codepipeline

## Parameters

`/ipa-codepipeline` prompts for configuration interactively.

| Parameter | Default | Description |
|-----------|---------|-------------|
| Repository name | `{namespace}-{env}-repo` | CodeCommit repository name |
| Branch | `main` | Source branch that triggers the pipeline |

**Prerequisites from `.env`:**

| Variable | Source |
|----------|--------|
| `APP_NAMESPACE` | `/ipa-init` |
| `APP_ENV` | `/ipa-init` |
| `AWS_ACCOUNT_ID` | `/ipa-init` |
| `AWS_REGION` | `/ipa-init` |
| `APP_CODEBUILD_ROLE_ARN` | `/ipa-compose` (security phase) |
| Composed Makefiles in `scripts/` | `/ipa-compose` |

## What It Does

1. **Pre-flight checks** — Verifies `.env` has init and compose prerequisites (including security variables from the compose security phase). Detects any existing pipeline.

2. **Source configuration** — Prompts for repository name and branch.

3. **Query prepare stacks** — Fetches ECR and Cognito stack outputs to inject as CodeBuild environment variables.

4. **Confirmation summary** — Displays the full configuration table before deployment.

5. **Deploy CodeCommit stack** — Creates `{namespace}-{env}-codecommit` with the source repository.

6. **Deploy CodePipeline stack** — Creates `{namespace}-{env}-codepipeline` with a four-stage pipeline:
   - **Test** — Runs `make -f scripts/test.mk test`
   - **Build** — Runs `make -f scripts/build.mk build`
   - **Deploy** — Runs `make -f scripts/deploy.mk deploy`
   - **PostDeploy** — Runs `make -f scripts/post-deploy.mk post-deploy`

7. **Write `.env` pipeline block** — Stores pipeline configuration variables.

8. **Completion report** — Displays pipeline URL, clone instructions, and buildspec details.

### Update Flow

When an existing pipeline is detected, the skill displays the current configuration and offers to re-query prepare stack outputs and update the pipeline.

## Outputs

| Artifact | Description |
|----------|-------------|
| CodeCommit stack | `{APP_NAMESPACE}-{APP_ENV}-codecommit` |
| CodePipeline stack | `{APP_NAMESPACE}-{APP_ENV}-codepipeline` |
| `.env` variables | `PIPELINE_STACK_NAME`, `PIPELINE_NAME`, `CODEBUILD_PROJECT_NAME`, `CODECOMMIT_STACK_NAME`, `CODECOMMIT_REPO_NAME`, `CODECOMMIT_CLONE_URL` |

## Examples

**Set up CI/CD for the first time:**

    /ipa-codepipeline

Provide a repository name and branch. The skill deploys CodeCommit and CodePipeline stacks, then displays the clone URL and pipeline URL.

**Update an existing pipeline:**

    /ipa-codepipeline

The skill detects the existing pipeline configuration and offers to update it with current prepare stack outputs.

## Related Skills

- [/ipa-init](./ipa-init.md) — Provides base `.env` variables
- [/ipa-compose](./ipa-compose.md) — Generates the Makefiles that the pipeline executes and provides the CodeBuild execution role (via embedded security phase)
- [/ipa-stack-codecommit](../stack-skills/ipa-stack-codecommit.md) — CodeCommit stack reference
- [/ipa-stack-codepipeline](../stack-skills/ipa-stack-codepipeline.md) — CodePipeline stack reference
