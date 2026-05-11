---
title: /ipa-help
sidebar_position: 9
---

# /ipa-help

Report IPA project state and suggest the next lifecycle skill to run.

## Purpose

`/ipa-help` is a diagnostic skill that inspects the current project state — filesystem artifacts, `.env` variables, and deployed CloudFormation stacks — and reports a one-line status with a suggested next skill. It does not modify files, deploy infrastructure, or invoke other skills.

## When to Use

Run `/ipa-help` when you are unsure where you are in the lifecycle or what to run next. It is particularly useful when returning to a project after time away or troubleshooting a deployment that stopped mid-pipeline.

## How It Works

The skill checks three layers of state:

1. **Filesystem** — Does `.env` exist? Does it contain IPA variables? Do `scripts/deploy.mk` and `scripts/prepare.mk` exist?
2. **Configuration** — Is `APP_BUILDER_ROLE_ARN` set (security configured)?
3. **AWS** — Are the security, prepare, and deploy stacks in `*_COMPLETE` status?

Based on these checks, it maps the project to one of six states and suggests the appropriate next skill.

## Decision Matrix

| State | Detection | Suggestion |
|-------|-----------|-----------|
| Not initialized | `.env` missing or `APP_NAMESPACE` absent | Run `/ipa-init` |
| Initialized, not composed | `.env` present, no `scripts/deploy.mk` | Run `/ipa-compose <stacks>` |
| Composed, security missing | `scripts/deploy.mk` present, `APP_BUILDER_ROLE_ARN` absent | Run `/ipa-compose` (triggers security phase) |
| Composed, not prepared | Prepare stacks defined but not deployed | Run `/ipa-prepare` |
| Prepared, not deployed | Prepare stacks active, deploy stacks missing | Run `/ipa-deploy` |
| Fully deployed | All stacks active | Deployment complete. Use `/ipa-destroy` to tear down. |

## Output Format

The skill produces a two-line response: one-line state summary, followed by a "Next:" line with the suggested command.

```
State: Initialized, not composed.
Next: Run `/ipa-compose frontend backend` to compose your infrastructure.
```

```
State: Fully deployed (all stacks active).
Next: Deployment complete. Use `/ipa-destroy` to tear down when done.
```

## Graceful Degradation

If AWS credentials are unavailable or API calls fail, the skill reports filesystem state only and notes "AWS status unavailable." It never blocks or errors — state detection degrades from full (filesystem + AWS) to partial (filesystem only).

## Scope

`/ipa-help` v1 reports state and suggests a single next skill. It does not:

- List individual stacks or their outputs
- Dump `.env` contents
- Offer troubleshooting guidance
- Auto-invoke any skill
