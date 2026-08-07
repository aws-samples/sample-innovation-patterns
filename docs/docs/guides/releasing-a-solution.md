---
title: Releasing a Solution
sidebar_position: 13
---

# Releasing a Solution

## Overview

This guide covers cutting a versioned release of a composed solution: deriving the version from commit history, writing a changelog, and creating an annotated tag. `/ipa-compose` generates `scripts/release.mk` and a root `cliff.toml` for exactly this, and both run on `make`, `git`, and `git-cliff` alone — no IPA, no Claude Code, and no forge required.

## When to Use This Guide

Use this guide when:

- A composed solution needs a versioned release to hand to a customer
- A customer asks how they will cut releases after the engagement ends
- Understanding what `scripts/release.mk` does is needed before running it

Do not use this guide to release the IPA framework itself — that has its own two-stage internal process. Do not use this guide to deploy infrastructure; releasing tags source code and has no effect on deployed stacks.

## Before You Start

- `/ipa-compose` has been run, so `scripts/release.mk` and `cliff.toml` exist
- `git-cliff` is installed — `brew install git-cliff`, or see [git-cliff.org](https://git-cliff.org)
- The repository has at least one commit

A remote is **not** required. Neither is a forge.

## Before / Target State

| Before | After |
|--------|-------|
| A composed solution with commit history and no releases, or with a previous release tag. | An annotated tag naming the derived version, carrying the release notes on its annotation; `CHANGELOG.md` written through that version and left uncommitted for review; the tag pushed and a forge Release created **if** a forge is configured. |

## Steps

### 1. Write commit messages that can be released

The version is derived from [Conventional Commits](https://www.conventionalcommits.org/) — it is not stored in a file and not typed by hand.

| Commit | Effect on the version | Changelog section |
|--------|----------------------|-------------------|
| `fix: ...` | patch bump | Fixed |
| `feat: ...` | minor bump | Added |
| `feat!: ...` | see the pre-1.0 note below | Added |
| `chore:`, `test:`, `style:` | none | (skipped) |
| anything non-conventional | **none** | **none** |

That last row is the one worth internalizing: a commit that matches no conventional type derives no bump *and* appears in no changelog section. The work still ships; nothing records that it did.

### 2. Preview the release

```bash
make -f scripts/release.mk release-preview
```

This prints the current tag, the version that would be cut, and the exact release notes. It creates nothing, so it is safe to run at any time.

```
current release: v0.1.0
would release:   v0.2.0

## [Unreleased]

### Added
- Add the widget

### Fixed
- Correct the sprocket
```

If it reports nothing to release, no commit since the last tag affects the version — usually because everything in the window is `chore:`-shaped.

### 3. Cut the release

```bash
make -f scripts/release.mk release
```

This writes `CHANGELOG.md`, creates the annotated tag, and — only if a forge is configured — pushes the tag and creates a Release object.

To release a specific version instead of the derived one:

```bash
make -f scripts/release.mk release VERSION=1.0.0
```

### 4. Review and commit the changelog

`CHANGELOG.md` is left uncommitted deliberately, because generated changelog entries usually benefit from a human pass. Review it, then:

```bash
git commit -am 'docs: update changelog'
```

The release notes also travel on the tag annotation, so the committed changelog is a convenience rather than a requirement.

## No Forge? Nothing Fails

A solution may have no remote and no forge CLI. Every forge-specific step **skips rather than fails**:

| Situation | What happens |
|-----------|--------------|
| No `origin` remote | Changelog written, tag created locally, you are told to push it later |
| Remote but no `gh`/`glab` | Tag pushed; no Release object, and you are told the annotation already carries the notes |
| `NO_PUSH=1` | Nothing pushed |

`make -f scripts/release.mk release` exits 0 in all three cases. A release target that failed without a forge would be unusable rather than merely limited.

## Pre-1.0 Versions

`cliff.toml` ships with `breaking_always_bump_major = false`, so while the major version is `0`, a `feat!:` commit derives `0.x+1` rather than `1.0.0`. Reaching a major becomes a deliberate act:

```bash
make -f scripts/release.mk release VERSION=1.0.0
```

This setting is **inert** once the major version reaches 1: after that, a breaking change derives the next major normally. Delete it from `cliff.toml` if you want `feat!:` to mean `1.0.0` immediately.

## Limitations

**Tag pushes do not trigger the generated CodePipeline.** The pipeline triggers on branch references only — `referenceType: [branch]` in both `infra/cfn/codepipeline/codepipeline.yml` and `infra/tf/codepipeline/main.tf` — so pushing a tag starts no build or deployment. Deploy by pushing to the tracked branch, and treat releasing as a separate act that marks a point in history.

This is documented rather than worked around: changing the trigger would touch a deployed CloudFormation template, its Terraform twin, the stack skill, and CloudFormation/Terraform parity, to enable something nothing currently asks for.

**`scripts/release.mk` is generated but not exercised by IPA's own tests**, the same class as the `scripts/test.mk` stub. Review it before relying on it for a customer-facing release.

**Compare links are not generated.** Tags and forge Release objects are the durable record. If published tags are ever a subset of internal tags, a compare link between adjacent changelog versions is a 404 by construction — so they are omitted rather than generated wrong.

## Troubleshooting

### `git-cliff is not installed`

```bash
brew install git-cliff
```

### `could not derive a version from commit history`

There are no commits, or `cliff.toml` is missing from the repository root. Re-run `/ipa-compose` if the file was deleted.

### `Nothing to release`

The derived version equals the current tag. Every commit in the window is configured to derive no bump. If the work deserves a release, it deserves a conventional commit message.

### `tag annotation lost its heading structure`

The release notes reached the tag through a path that stripped Markdown headings — `git tag -a -m` deletes every `#`-leading line as a comment and exits 0. The generated target uses `--cleanup=verbatim -F <file>` and asserts afterwards, deleting the tag rather than shipping a flattened body. If you see this, `release.mk` has been edited; restore the `--cleanup=verbatim` flag.

## Next Steps

- [Path to Production](path-to-production.md) — hardening a POC for real workloads
- [Testing](testing.md) — adding real tests to the generated `scripts/test.mk` stub

To adopt this release standard in a project that was not composed by IPA, copy `scripts/release.mk` and `cliff.toml` out of any composed solution — neither contains IPA-specific values, and together they are the whole practice.
