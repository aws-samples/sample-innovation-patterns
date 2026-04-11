---
title: Overview
sidebar_position: 1
---

# Lifecycle Skills

Lifecycle skills orchestrate the IPA project workflow from initialization through deployment and teardown. They run in a defined sequence, with each skill producing the configuration or infrastructure that the next skill consumes.

## Standard Workflow

```
/ipa.init → /ipa.security → /ipa.compose → /ipa.prepare → /ipa.deploy
```

## Skills Reference

| Skill | Purpose |
|-------|---------|
| [/ipa.init](./ipa-init.md) | Configure project environment variables |
| [/ipa.security](./ipa-security.md) | Provision IAM roles and log bucket |
| [/ipa.compose](./ipa-compose.md) | Generate deployment Makefiles from pattern definitions |
| [/ipa.prepare](./ipa-prepare.md) | Deploy one-time prerequisite stacks (ECR, Cognito) |
| [/ipa.deploy](./ipa-deploy.md) | Deploy the composed infrastructure pattern |
| [/ipa.destroy](./ipa-destroy.md) | Tear down deployed pattern stacks |
| [/ipa.codepipeline](./ipa-codepipeline.md) | Deploy CI/CD pipeline (CodeCommit + CodePipeline) |
