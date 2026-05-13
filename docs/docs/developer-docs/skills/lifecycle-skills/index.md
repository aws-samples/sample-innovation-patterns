---
title: Overview
sidebar_position: 1
---

# Lifecycle Skills

Lifecycle skills orchestrate the IPA project workflow from initialization through deployment and teardown. They run in a defined sequence, with each skill producing the configuration or infrastructure that the next skill consumes.

## Standard Workflow

```
/ipa-init → /ipa-compose → /ipa-prepare → /ipa-deploy
```

## Skills Reference

| Skill | Purpose |
|-------|---------|
| [/ipa-init](./ipa-init.md) | Configure project environment variables |
| [/ipa-compose](./ipa-compose.md) | Generate deployment Makefiles from pattern definitions. Embeds security provisioning on first compose. |
| [/ipa-prepare](./ipa-prepare.md) | Deploy one-time prerequisite stacks (log bucket, ECR, Cognito) |
| [/ipa-deploy](./ipa-deploy.md) | Deploy the composed infrastructure pattern |
| [/ipa-destroy](./ipa-destroy.md) | Tear down deployed pattern stacks |
| [/ipa-help](./ipa-help.md) | Report project state and suggest the next lifecycle skill |
| [/ipa-security](./ipa-security.md) | Backing skill for IAM provisioning (embedded in `/ipa-compose`; also usable standalone for switching configuration paths) |
| [/ipa-codepipeline](./ipa-codepipeline.md) | ~~Deploy CI/CD pipeline~~ **Deprecated** — use `/ipa-compose codepipeline` + `/ipa-prepare` |
