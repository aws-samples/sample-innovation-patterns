---
title: /ipa.author.stack
sidebar_position: 2
---

# /ipa.author.stack

Create or update IPA stack skills, CloudFormation templates, and pattern definitions. Supports single-service prepare stacks, multi-service tier stacks, and pattern-only definitions.

## Invocation

    /ipa.author.stack

## Parameters

`/ipa.author.stack` gathers all parameters interactively through a requirements phase. No arguments are passed at invocation.

| Input | Description |
|-------|-------------|
| Architecture overview | High-level description of the stack's purpose and AWS services |
| Stack type | Single-service (prepare) or multi-service (tier) |
| AWS services | Services to include in the CloudFormation template |
| Parameters | Stack parameters with types, defaults, and validation |
| Feature flags | Optional boolean parameters that toggle resource creation |
| Outputs | Stack outputs with export names |
| Capabilities | CloudFormation capabilities required (e.g., `CAPABILITY_NAMED_IAM`) |
| Build requirements | Container or asset build steps |
| Security posture | Security configuration and findings |
| Lifecycle | `prepare` or `deploy` |
| Dependencies | Other stacks this stack depends on or provides outputs to |
| Config overrides | Parameter overrides for pattern composition |
| Post-deploy steps | Operations to run after stack deployment |

## What It Does

The skill executes five phases:

### Phase 1 — Gather Requirements

Collects the architecture overview, stack selection, AWS services, parameters, feature flags, outputs, capabilities, build requirements, security posture, lifecycle, dependencies, config overrides, and post-deploy steps through interactive prompts.

### Phase 2 — Create CloudFormation Template

Generates a YAML CloudFormation template at `infra/cfn/{service}/{service}.yml`. Validates the template with `aws cloudformation validate-template`.

### Phase 3 — Create Stack Skill Files

Creates three files in `.claude/skills/ipa.stack.{service}/`:

| File | Purpose |
|------|---------|
| `SKILL.md` | Stack skill definition with frontmatter, parameters, outputs, wiring, and lifecycle |
| `SECURITY.md` | Security findings and dispositions |
| `TROUBLESHOOT.md` | Common deployment errors and resolutions |

### Phase 4 — Create Pattern Definition

Creates two files in `.claude/skills/ipa.compose/patterns/{name}/`:

| File | Purpose |
|------|---------|
| `PATTERN.md` | Stack sequence, wiring, teardown sequence, known deferrals, post-deploy |
| `ARCHITECTURE.md` | Architecture diagram and resource descriptions |

### Phase 5 — Validate

Checks stack-to-SKILL.md consistency, CloudFormation contract compliance, and pattern integrity.

## Authoring Modes

| Mode | When to Use |
|------|-------------|
| **Combined** (default) | Creating a new tier stack with a pattern definition |
| **Single-service** | Creating a one-AWS-service prepare stack (ECR, Cognito, SNS, RDS, SES) |
| **Pattern-only** | Creating a pattern definition for existing stacks |
| **Update** | Modifying existing stack skill files or patterns |

## Outputs

| Artifact | Path | Description |
|----------|------|-------------|
| CloudFormation template | `infra/cfn/{service}/{service}.yml` | Infrastructure template |
| Stack skill | `.claude/skills/ipa.stack.{service}/SKILL.md` | Skill definition |
| Security doc | `.claude/skills/ipa.stack.{service}/SECURITY.md` | Security findings |
| Troubleshooting doc | `.claude/skills/ipa.stack.{service}/TROUBLESHOOT.md` | Error resolution guide |
| Pattern definition | `.claude/skills/ipa.compose/patterns/{name}/PATTERN.md` | Compose pattern |
| Architecture doc | `.claude/skills/ipa.compose/patterns/{name}/ARCHITECTURE.md` | Architecture reference |

## Examples

**Create a new tier stack with pattern:**

    /ipa.author.stack

Describe a notification service using SNS and Lambda. The skill creates the CloudFormation template, stack skill files, and a pattern definition.

**Add a single-service prepare stack:**

    /ipa.author.stack

Describe an RDS database as a single-service prepare stack. The skill creates the template and stack skill without a pattern definition.

## Related Skills

- [/ipa.compose](../ipa-compose.md) — Consumes the stack skills and patterns created by this skill
- [/ipa.deploy](../ipa-deploy.md) — Deploys stacks defined by authored skills
