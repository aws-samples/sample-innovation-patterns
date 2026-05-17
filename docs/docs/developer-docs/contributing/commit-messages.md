---
title: Commit Messages
sidebar_position: 20
---

# Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages. This convention enables automated CHANGELOG generation via [git-cliff](https://git-cliff.org/) and makes the commit history scannable at a glance.

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

The project uses [git-cliff](https://git-cliff.org/) to generate `CHANGELOG.md` from Conventional Commit history. Configuration is in [`cliff.toml`](https://github.com/aws-samples/sample-innovation-patterns/blob/main/cliff.toml) at the repo root.

Non-conventional commits (from before this convention was adopted) are preserved in the CHANGELOG under "Changed" rather than dropped.
