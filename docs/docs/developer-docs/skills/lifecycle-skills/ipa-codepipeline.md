---
title: /ipa-codepipeline
sidebar_position: 8
---

# /ipa-codepipeline — DEPRECATED

:::warning
This skill is deprecated. CodePipeline is now a composable prepare stack managed by `/ipa-compose`.
:::

## Migration

The CodePipeline and CodeCommit stacks are now integrated into `/ipa-compose` as prepare-lifecycle stacks. Instead of running `/ipa-codepipeline`, use:

1. `/ipa-compose codepipeline` — adds codecommit + codepipeline to the composition
2. `/ipa-prepare` — deploys all prepare stacks (including codecommit + codepipeline)

## Existing Deployments

If CI/CD was previously deployed via `/ipa-codepipeline`, the stacks are compatible. Re-run `/ipa-compose` to include them in the composition, then `/ipa-prepare` to align with the compose-managed flow. Stack names are unchanged.

## Related Skills

- [/ipa-compose](./ipa-compose.md) — Composes infrastructure including codepipeline stacks
- [/ipa-prepare](./ipa-prepare.md) — Deploys prepare stacks
- [/ipa-stack-codecommit](../stack-skills/ipa-stack-codecommit.md) — CodeCommit stack reference
- [/ipa-stack-codepipeline](../stack-skills/ipa-stack-codepipeline.md) — CodePipeline stack reference
