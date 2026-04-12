---
title: CI/CD with CodePipeline
sidebar_position: 5
---

# CI/CD with CodePipeline

## Overview

This guide configures a CI/CD pipeline using AWS CodePipeline and CodeBuild that automates the build, test, and deploy cycle for an IPA composition. By the end, the reader has a 5-stage pipeline (Source, Test, Build, Deploy, PostDeploy) that triggers on CodeCommit pushes and executes the same Makefile targets the builder runs locally.

## When to Use This Guide

Use this guide when:

- The composition is stable and deployed at least once with `/ipa.deploy`, and the team is ready to automate the build-test-deploy cycle
- The customer requires CI/CD as a project deliverable
- The project is transitioning from manual `/ipa.deploy` invocations to push-triggered deployments
- A staging or production environment needs continuous delivery from a shared repository

Do not use this guide if the composition has not been deployed successfully at least once — stabilize the manual workflow first.

## Before You Start

Before you start, confirm the following:

- `/ipa.init` completed — `.env` contains `APP_NAMESPACE`, `APP_ENV`, `AWS_ACCOUNT_ID`, and `AWS_REGION`
- `/ipa.security` completed — `.env` contains `APP_CODEBUILD_ROLE_ARN`
- `/ipa.compose` completed — `scripts/` directory contains generated Makefiles (`deploy.mk`, `build.mk`, `test.mk`, `post-deploy.mk`)
- `/ipa.prepare` completed — ECR and Cognito stacks are deployed in the target account
- `/ipa.deploy` completed at least once — the composition deploys successfully from local Makefile targets
- AWS CLI configured with credentials that have `iam:CreateRole` and `iam:PassRole` permissions (required for pipeline IAM roles)

## Before / Target State

| Before | After |
|--------|-------|
| Manually deployed IPA composition. Code changes require the builder to run `/ipa.deploy`. | 5-stage CodePipeline triggered automatically on every push to the configured branch. |
| No shared source repository. | CodeCommit repository with HTTPS clone URL. |
| No CI/CD infrastructure. | CodePipeline, CodeBuild project, S3 artifact bucket, and EventBridge trigger rule deployed via CloudFormation. |
| `.env` has no pipeline variables. | `.env` updated with `PIPELINE_STACK_NAME`, `PIPELINE_NAME`, `CODEBUILD_PROJECT_NAME`, `CODECOMMIT_STACK_NAME`, `CODECOMMIT_REPO_NAME`, and `CODECOMMIT_CLONE_URL`. |

## Steps

### 1. Verify prerequisites

To confirm the composition is ready for CI/CD automation, check that the required stacks are deployed and the Makefiles exist.

Verify the ECR stack:

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name ${APP_NAMESPACE}-${APP_ENV}-ecr \
  --query 'Stacks[0].StackStatus' \
  --output text
```

The command outputs `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

Verify the Cognito stack:

```bash
source .env 2>/dev/null; aws cloudformation describe-stacks \
  --stack-name ${APP_NAMESPACE}-${APP_ENV}-cognito \
  --query 'Stacks[0].StackStatus' \
  --output text
```

The command outputs `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

Verify the Makefiles exist:

```bash
ls scripts/deploy.mk scripts/build.mk scripts/test.mk scripts/post-deploy.mk
```

All four files are listed. If any prerequisite is missing, complete the corresponding skill (`/ipa.init`, `/ipa.security`, `/ipa.compose`, `/ipa.prepare`) before continuing.

### 2. Run /ipa.codepipeline

To deploy the pipeline infrastructure, invoke the codepipeline skill:

```
/ipa.codepipeline
```

The skill performs the following:

1. Validates `.env` prerequisites (init variables, CodeBuild role, Makefiles)
2. Prompts for a **repository name** (default: `{APP_NAMESPACE}-{APP_ENV}-repo`) and **trigger branch** (default: `main`)
3. Queries the ECR and Cognito stacks for output values needed as CodeBuild environment variables
4. Displays a confirmation summary with all settings and their sources
5. Deploys the **CodeCommit stack** (`infra/cfn/codecommit/codecommit.yml`) — creates the source repository
6. Deploys the **CodePipeline stack** (`infra/cfn/codepipeline/codepipeline.yml`) — creates the pipeline, CodeBuild project, artifact bucket, and EventBridge trigger
7. Writes pipeline variables to `.env`

When both stacks deploy successfully, the skill displays the pipeline console URL, clone URL, and push instructions.

### 3. Review the pipeline stages

The deployed pipeline has five stages. Each stage runs the corresponding Makefile target in a CodeBuild environment with the same environment variables the builder uses locally.

| Stage | Makefile | Target | Purpose |
|-------|----------|--------|---------|
| Source | — | — | Pulls source code from the CodeCommit repository |
| Test | `test.mk` | `test` | Runs unit and integration tests |
| Build | `build.mk` | `build` | Builds application artifacts (Docker images, frontend bundles) |
| Deploy | `deploy.mk` | `deploy` | Deploys CloudFormation stacks to the target environment |
| PostDeploy | `post-deploy.mk` | `post-deploy` | Runs post-deployment tasks (cache invalidation, smoke tests) |

The buildspec is inline in the CloudFormation template — no `buildspec.yml` file is needed in the repository. Each stage overrides the `IPA_MAKEFILE` and `IPA_TARGET` environment variables to select the correct Makefile and target.

:::note
The CodeBuild project installs Python 3.12, Node.js 22, and `uv` in the install phase of every stage. Privileged mode is enabled for Docker builds.
:::

### 4. Push source code to CodeCommit

To add the CodeCommit repository as a remote and push the source code, run:

```bash
git remote add codecommit $(grep CODECOMMIT_CLONE_URL .env | cut -d= -f2)
git push codecommit main
```

Replace `main` with the branch name configured in step 2 if a different branch was selected.

:::warning
The pipeline triggers automatically on the first push. Verify that all Makefile targets pass locally before pushing to avoid a failed initial pipeline run.
:::

### 5. Monitor the pipeline

To check the pipeline status from the CLI, run:

```bash
source .env 2>/dev/null; aws codepipeline get-pipeline-state \
  --name ${PIPELINE_NAME} \
  --query 'stageStates[].{Stage:stageName,Status:latestExecution.status}' \
  --output table
```

The command outputs a table showing each stage and its current status (`InProgress`, `Succeeded`, or `Failed`).

To view the pipeline in the AWS Console, open:

```
https://{AWS_REGION}.console.aws.amazon.com/codesuite/codepipeline/pipelines/{PIPELINE_NAME}/view
```

Replace `{AWS_REGION}` and `{PIPELINE_NAME}` with the values from `.env`.

### 6. Trigger subsequent pipeline runs

After the initial push, the pipeline triggers automatically on every push to the configured branch. The EventBridge rule watches for `referenceCreated` and `referenceUpdated` events on the CodeCommit repository and starts a new pipeline execution.

To trigger a pipeline run manually without pushing code, run:

```bash
source .env 2>/dev/null; aws codepipeline start-pipeline-execution \
  --name ${PIPELINE_NAME}
```

The command outputs the pipeline execution ID.

## Verification

To verify the pipeline is deployed and all stages succeeded, run:

```bash
source .env 2>/dev/null; aws codepipeline get-pipeline-state \
  --name ${PIPELINE_NAME} \
  --query 'stageStates[].{Stage:stageName,Status:latestExecution.status}' \
  --output table
```

Expected output after a successful run:

```
---------------------------
|    GetPipelineState     |
+------------+------------+
|   Stage    |  Status    |
+------------+------------+
|  Source    |  Succeeded |
|  Test      |  Succeeded |
|  Build     |  Succeeded |
|  Deploy    |  Succeeded |
|  PostDeploy|  Succeeded |
+------------+------------+
```

Verify the deployed application is functional by testing its endpoints. The deploy stage executed the same `deploy.mk` targets as a local `/ipa.deploy`, so the application state should match a local deployment.

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Stack creation fails with "Role ARN does not exist" on CodeBuildProject | The `APP_CODEBUILD_ROLE_ARN` in `.env` references a role that does not exist or was deleted. | Run `/ipa.security` to create the CodeBuild execution role. Verify `APP_CODEBUILD_ROLE_ARN` in `.env` matches the security stack output. |
| Stack creation fails with "BucketAlreadyExists" | The S3 artifact bucket name `{namespace}-{env}-pipeline-artifacts-{account_id}` collides with an existing bucket. S3 bucket names are globally unique. | Change `APP_NAMESPACE` via `/ipa.init` to produce a different bucket name, or delete the existing bucket if it is unused. |
| Pipeline Source stage fails with "Repository not found" | The CodeCommit repository referenced by `SourceRepoName` does not exist, or the codecommit stack failed to deploy. | Verify the codecommit stack deployed successfully: `source .env 2>/dev/null; aws cloudformation describe-stacks --stack-name ${APP_NAMESPACE}-${APP_ENV}-codecommit`. Re-run `/ipa.codepipeline` if the stack is missing. |
| CodeBuild stages fail with empty environment variables (`ECR_REPO_URI`, `OIDC_ISSUER`) | The prepare stacks (ECR, Cognito) were redeployed with different outputs after the pipeline was created, but the pipeline stack was not updated. | Re-run `/ipa.codepipeline` and select "Yes, update" to re-query prepare-stack outputs and update the pipeline stack. |
| Pipeline triggers immediately after creation before code is pushed | This is expected behavior. EventBridge may trigger on initial repository state. The Test stage fails because no source code exists. | Push code to the CodeCommit repository. The next pipeline run will succeed. The initial auto-trigger failure is harmless. |

## Next Steps

- **Harden for production** — see [Path to Production](path-to-production.md) for configuration changes, security hardening, and customer handoff procedures
- **CodePipeline stack reference** — see the stack skill documentation at `.claude/skills/ipa.stack.codepipeline/` for template parameters, outputs, and resource details
- **CodeCommit stack reference** — see the stack skill documentation at `.claude/skills/ipa.stack.codecommit/` for repository configuration options
- **Tear down the pipeline** — run `/ipa.destroy` to remove the pipeline and repository stacks (see [the destroy skill documentation](/developer-docs/skills/lifecycle-skills/ipa-destroy))
- **Update the pipeline** — re-run `/ipa.codepipeline` at any time to update the pipeline configuration with current prepare-stack outputs
