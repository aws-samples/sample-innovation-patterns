---
title: /ipa.stack.ecr
sidebar_position: 6
---

# /ipa.stack.ecr

ECR repository for container image storage. A prepare-lifecycle stack that persists across deploy/destroy cycles.

## Stack Identity

| Property | Value |
|----------|-------|
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-ecr` |
| Template | `infra/cfn/ecr/ecr.yml` |
| Capabilities | None |
| Lifecycle | prepare |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `Namespace` | *(from `.env`)* | Project namespace |
| `Environment` | *(from `.env`)* | Environment label |

## Outputs

| Output | Description |
|--------|-------------|
| `RepositoryUri` | ECR repository URI for container images |
| `RepositoryArn` | Repository ARN for security policy scoping |

## Security

- Encryption at rest: AES-256
- No public access
- No automatic deletion (images persist until manually removed)

## Wiring

Other stacks consume ECR outputs:

| Consumer | Parameter Wired |
|----------|----------------|
| Backend | `ImageUri` ← `RepositoryUri` |
| Queue | `ImageUri` ← `RepositoryUri` |
| CodePipeline | `EcrRepoUri` ← `RepositoryUri` |

## Related Skills

- [/ipa.prepare](../lifecycle-skills/ipa-prepare.md) — Deploys this stack
- [/ipa.stack.backend](./ipa-stack-backend.md) — Consumes image URI
- [/ipa.stack.queue](./ipa-stack-queue.md) — Consumes image URI
- [/ipa.stack.codepipeline](./ipa-stack-codepipeline.md) — Consumes image URI for builds
