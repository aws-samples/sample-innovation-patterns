---
title: Overview
sidebar_position: 1
---

# Stack Skills

Stack skills define individual CloudFormation stacks that `/ipa.compose` assembles into deployment patterns. Each stack skill lives at `.claude/skills/ipa.stack.{name}/SKILL.md` and declares the stack's parameters, outputs, wiring, feature flags, and lifecycle classification.

Stack skills are not invoked directly. Instead, `/ipa.compose` reads them to generate Makefiles and deployment configuration.

## Lifecycle Classification

Stacks are classified into two lifecycle categories that determine when they are deployed and whether `/ipa.destroy` removes them:

| Lifecycle | Deployed By | Removed By | Examples |
|-----------|-------------|------------|----------|
| **prepare** | `/ipa.prepare` | Manual (`make -f scripts/prepare.mk teardown-prepare`) | ECR, Cognito |
| **deploy** | `/ipa.deploy` | `/ipa.destroy` | Backend, Frontend, Queue |

## Solution Tier Stacks

These stacks form the application infrastructure and are deployed and destroyed as a unit.

| Stack | Description |
|-------|-------------|
| [/ipa.stack.backend](./ipa-stack-backend.md) | Lambda + API Gateway v2 + DynamoDB + CloudWatch |
| [/ipa.stack.frontend](./ipa-stack-frontend.md) | S3 + CloudFront + OAC |
| [/ipa.stack.queue](./ipa-stack-queue.md) | SQS + DLQ + worker Lambda + DynamoDB + CloudWatch |

## Prepare Stacks

These stacks provide shared prerequisites and persist across deploy/destroy cycles.

| Stack | Description |
|-------|-------------|
| [/ipa.stack.ecr](./ipa-stack-ecr.md) | ECR repository for container images |
| [/ipa.stack.cognito](./ipa-stack-cognito.md) | Cognito User Pool with OAuth 2.0 and OIDC |

## Infrastructure Stacks

These stacks support CI/CD and are managed by `/ipa.codepipeline`.

| Stack | Description |
|-------|-------------|
| [/ipa.stack.codecommit](./ipa-stack-codecommit.md) | CodeCommit repository for source code |
| [/ipa.stack.codepipeline](./ipa-stack-codepipeline.md) | CodePipeline CI/CD with CodeBuild |
