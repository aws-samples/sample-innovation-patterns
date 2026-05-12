---
name: ipa-codepipeline
description: "[DEPRECATED] Use /ipa-compose codepipeline + /ipa-prepare instead."
---

# /ipa-codepipeline — DEPRECATED

> **This skill is deprecated.** CodePipeline is now a composable prepare stack.
> Use the standard compose+prepare flow instead.

## Migration

The CodePipeline and CodeCommit stacks are now integrated into `/ipa-compose` as
prepare-lifecycle stacks. Instead of running `/ipa-codepipeline`, use:

1. `/ipa-compose codepipeline` — adds codecommit + codepipeline to your composition
2. `/ipa-prepare` — deploys all prepare stacks (including codecommit + codepipeline)

## Existing Deployments

If you previously deployed CI/CD via `/ipa-codepipeline`, the stacks are compatible.
Re-run `/ipa-compose` to include them in your composition, then `/ipa-prepare` to
align with the compose-managed flow. Stack names are unchanged.
