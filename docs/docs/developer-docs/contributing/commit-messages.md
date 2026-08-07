---
title: Commit Messages
sidebar_position: 20
---

# Commit Messages

Every commit message must use [Conventional Commits](https://www.conventionalcommits.org/) format. This is not a style preference — the format is the input to two automated outputs:

1. **Version derivation.** The next release version is computed from commit history, not read from a file. A `fix:` commit produces a patch bump and `feat:` a minor bump; a commit matching no conventional type produces **no bump at all**.
2. **Published release notes.** The GitHub Release body is generated from these messages. A non-conventional commit lands in **no** changelog section and is invisible to anyone reading the release.

A commit written as `Update: modify 7 file(s)` is skipped by both. The work still ships — nothing records that it did.

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Rules:**
- **Description:** imperative mood, lowercase start, no trailing period, max 72 characters
- **Body:** wrap at 72 characters, explain WHY not WHAT
- **Multi-scope changes:** omit scope — `feat: add passenger job queue`

## Types

| Type | When to use | CHANGELOG section |
|------|-------------|-------------------|
| `feat` | New feature or capability | Added |
| `fix` | Bug fix | Fixed |
| `docs` | Documentation only | Documentation |
| `ci` | CI/CD pipeline changes | CI/Build |
| `refactor` | Code restructuring (no behavior change) | Changed |
| `style` | Formatting, whitespace (no code change) | (skipped) |
| `test` | Adding or updating tests | (skipped) |
| `chore` | Maintenance, dependency updates | (skipped) |
| `perf` | Performance improvements | Performance |
| `build` | Build system or external dependency changes | CI/Build |
| `revert` | Reverting a previous commit | Reverted |

## Scopes

Scopes are optional. Use one when the change is clearly limited to a single area:

| Scope | Area |
|-------|------|
| `ipa` | IPA skills framework (`.claude/skills/`, `scripts/`) |
| `app-lib` | Python backend library (`app-lib/`) |
| `web-client` | React frontend (`web-client/`) |
| `docs` | Documentation site (`docs/`) |
| `infra` | CloudFormation templates (`infra/cfn/`) |

## Examples

```
feat(ipa): add logs stack for centralized S3 log bucket
fix(web-client): resolve OIDC token refresh race condition
docs: update releasing guide for trunk-based workflow
ci: add manual tag-and-release trigger
refactor(app-lib): extract AbstractDataService from passenger service
chore: bump FastAPI to 0.115.12
build(infra): consolidate backend tier template parameters
perf(app-lib): cache DynamoDB table name resolution
```

## Breaking Changes

Append `!` after the type/scope to signal a breaking change:

```
feat(app-lib)!: change API response format

BREAKING CHANGE: The /api/passengers endpoint now returns paginated
results instead of a flat array. Clients must handle the new
{ items: [], next_token: string } shape.
```

Both the `!` suffix and the `BREAKING CHANGE:` footer are recognized. Use `!` for the subject line; use the footer to describe the migration path.

## Release Commits

When preparing a release, use:

```
chore: release v0.2.0
```

## Tooling

The project uses [git-cliff](https://git-cliff.org/) to generate `CHANGELOG.md` from Conventional Commit history, and to derive the next version from it. Configuration is in [`cliff.toml`](https://github.com/aws-samples/sample-innovation-patterns/blob/main/cliff.toml) at the repo root.

Two configured behaviors are worth knowing:

- **`Update:`-prefixed commits are skipped.** A batch of diffstat-shaped messages predating this convention would otherwise fill the changelog with entries like "modify 7 file(s)". They are filtered out rather than grouped.
- **A breaking change stays within `0.x` while the project is pre-1.0.** A `feat!:` commit derives `0.x+1`, not `1.0.0`. Reaching `1.0.0` is a deliberate, separately confirmed act. Once the major version reaches 1, a breaking change derives the next major as usual.

## Where This Convention Pays Off

The release standard is what consumes these messages. Composed solutions receive the same practice as generated artifacts (`scripts/release.mk` and a root `cliff.toml`), so the convention is worth following in customer projects too, not just here.

See [Releasing a Solution](../../guides/releasing-a-solution.md) for how a version is derived, what the generated release target does, and why it works with no forge at all.
