---
title: Overview
sidebar_position: 1
---

# CodePipeline

The CodePipeline stack deploys a fully automated CI/CD pipeline using AWS CodePipeline and AWS CodeBuild. It provisions a five-stage pipeline (Source, Test, Build, Deploy, PostDeploy) that executes the same Makefiles used during local development, ensuring parity between local and automated workflows. An EventBridge rule triggers the pipeline on every push to the tracked branch in CodeCommit, replacing polling-based source detection. All pipeline artifacts are stored in a private, encrypted S3 bucket with public access blocked and non-SSL requests denied.

**Template:** `infra/cfn/codepipeline/codepipeline.yml`
**Lifecycle:** prepare (one-time)
**Capabilities:** `CAPABILITY_NAMED_IAM`

## Five-Stage Pipeline

The pipeline progresses through five sequential stages, each invoking the same CodeBuild project with different environment variable overrides:

1. **Source** -- Pulls the latest commit from CodeCommit via EventBridge trigger (no polling).
2. **Test** -- Executes `scripts/test.mk` with the `test` target.
3. **Build** -- Executes `scripts/build.mk` with the `build` target.
4. **Deploy** -- Executes `scripts/deploy.mk` with the `deploy` target.
5. **PostDeploy** -- Executes `scripts/post-deploy.mk` with the `post-deploy` target.

Each stage overrides the `IPA_MAKEFILE` and `IPA_TARGET` environment variables on the shared CodeBuild project. The inline buildspec runs `make -f "scripts/${IPA_MAKEFILE}" ${IPA_TARGET}`, preserving the Makefile-as-contract pattern throughout the pipeline.

## Features

- **Makefile-as-contract execution** -- pipeline stages invoke the same Make targets used for local development, eliminating drift between local and CI workflows
- **EventBridge push trigger** -- an EventBridge rule monitors CodeCommit for branch pushes, starting the pipeline within seconds of a commit (no polling interval)
- **Artifact encryption** -- the artifact bucket uses SSE-S3 by default with optional KMS encryption via the `KmsKeyArn` parameter
- **Scoped IAM roles** -- the PipelineRole restricts permissions to specific resource ARNs (CodeBuild project, artifact bucket, CodeCommit repository, optional KMS key); no wildcard resource policies
- **External CodeBuild execution role** -- the CodeBuild project uses a role provisioned by `/ipa.security`, separating pipeline orchestration permissions from build-time permissions
- **Privileged mode** -- CodeBuild runs with privileged mode enabled, required for Docker-in-Docker image builds
- **Inline buildspec** -- the buildspec is embedded in the CloudFormation template; no external `buildspec.yml` file is required
- **Public access blocked** -- the artifact bucket enables all four S3 PublicAccessBlock flags and enforces SSL-only access through a bucket policy

## When to Use

The CodePipeline stack is optional infrastructure deployed after the initial application stacks are operational. It is appropriate when the team requires automated CI/CD triggered by source commits. The stack depends on a CodeCommit repository (provisioned by the CodeCommit stack), an ECR repository (for container image URIs), a Cognito user pool (for OIDC parameters passed to build-time environment variables), and a CodeBuild execution role (from `/ipa.security`). If the project does not require automated pipelines -- for example, during early prototyping or when using an external CI/CD system -- this stack is not needed.
