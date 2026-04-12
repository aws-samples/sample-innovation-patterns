---
title: CI/CD with CodePipeline
sidebar_position: 5
---

# CI/CD with CodePipeline

:::info[Authoring Guidance]
This is a stub. Generate the full guide with the aidoc workflow or author directly using the guidance below each heading.
:::

## Overview

> **Guidance:** 1-2 sentences. This guide configures a CI/CD pipeline using AWS CodePipeline and CodeBuild that automates the build, test, and deploy cycle. By the end, the reader has a pipeline that triggers on CodeCommit pushes and executes the same Makefile targets the builder runs locally — build, deploy, post-deploy, and test.

## When to Use This Guide

> **Guidance:** 2-4 bullet points covering: composition is stable and ready for automation; customer requires CI/CD as a deliverable; moving from manual /ipa.deploy to push-triggered deployments; setting up staging or production with continuous delivery.

## Before You Start

> **Guidance:** Prerequisites: /ipa.compose completed, /ipa.prepare and /ipa.deploy completed at least once, CodeCommit stack deployed, source code pushed to CodeCommit, .env configured, familiarity with Makefile targets in scripts/.

## Before / Target State

> **Guidance:** Before: Manually deployed IPA composition. Code changes require builder to run /ipa.deploy. CodeCommit repository exists with source pushed. After: 5-stage CodePipeline (Source, Build, Deploy, PostDeploy, Test) triggered by CodeCommit pushes. Every push runs the full cycle automatically using the generated Makefiles.

## Steps

> **Guidance:** 6 steps. Source files: .claude/skills/ipa.codepipeline/SKILL.md, infra/cfn/codepipeline/codepipeline.yml (13 params, 5 stages), infra/cfn/codecommit/codecommit.yml, docs/docs/stacks/codepipeline/ (stack reference).

### 1. Verify prerequisites

> **Guidance:** Confirm CodeCommit is deployed, source is pushed, and the composition is stable.

### 2. Run /ipa.codepipeline

> **Guidance:** Invoke the skill. Explain what it generates and configures.

### 3. Review the generated pipeline template

> **Guidance:** Walk through the 5 pipeline stages: Source, Build, Deploy, PostDeploy, Test. Explain that each stage runs the corresponding Makefile target.

### 4. Deploy the pipeline stack

> **Guidance:** Deploy the CodePipeline CloudFormation stack. Explain the parameters that wire it to CodeCommit and existing stacks.

### 5. Trigger a pipeline run

> **Guidance:** Push a code change to CodeCommit and observe the pipeline executing.

### 6. Monitor the pipeline

> **Guidance:** Show how to check pipeline status via AWS Console or CLI.

## Verification

> **Guidance:** aws codepipeline get-pipeline-state to confirm all stages succeeded. Check the deployed application. Verify the test stage passed.

## Troubleshooting

> **Guidance:** Conditional section. Potential entries: build stage fails with missing dependencies; deploy stage IAM permission errors; source stage stuck on branch name mismatch; pipeline not triggering on push.

## Next Steps

> **Guidance:** Link to path-to-production guide, stacks/codepipeline/ reference, stacks/codecommit/ reference, /ipa.destroy documentation.
