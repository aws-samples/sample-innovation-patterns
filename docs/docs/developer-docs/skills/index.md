---
title: Overview
sidebar_position: 1
---

# Skills

IPA skills are Claude Code slash commands that automate infrastructure provisioning, deployment, and project management. Each skill is invoked with `/ipa.{name}` and performs a specific operation in the IPA workflow.

Skills are divided into three categories:

## Process Skills

Process skills orchestrate multi-step workflows. They run in a defined sequence to take a project from initialization through deployment.

| Skill | Purpose |
|-------|---------|
| [/ipa.init](./ipa-init.md) | Configure project environment variables |
| [/ipa.security](./ipa-security.md) | Provision IAM roles and log bucket |
| [/ipa.compose](./ipa-compose.md) | Generate deployment Makefiles from pattern definitions |
| [/ipa.prepare](./ipa-prepare.md) | Deploy one-time prerequisite stacks (ECR, Cognito) |
| [/ipa.deploy](./ipa-deploy.md) | Deploy the composed infrastructure pattern |
| [/ipa.destroy](./ipa-destroy.md) | Tear down deployed pattern stacks |
| [/ipa.codepipeline](./ipa-codepipeline.md) | Deploy CI/CD pipeline (CodeCommit + CodePipeline) |

The standard workflow order is: `/ipa.init` → `/ipa.security` → `/ipa.compose` → `/ipa.prepare` → `/ipa.deploy`.

## Stack Skills

Stack skills define individual CloudFormation stacks. They are consumed by `/ipa.compose` to generate deployment artifacts — they are not invoked directly by users.

- **[Stack Skills](./stack-skills/)** — Per-stack reference for backend, frontend, queue, ECR, Cognito, CodeCommit, and CodePipeline

## Author Skills

Author skills create new stack skills and pattern definitions for extending IPA with custom infrastructure.

- **[Author Skills](./author-skills/)** — Tools for creating and updating stack skills and patterns
