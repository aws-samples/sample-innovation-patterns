# innovation-patterns Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-10

## Active Technologies
- Markdown (Claude Code skill format) + Claude Code skill framework, AWS CLI (002-ipa-security-skill)
- `.env` (local config file), CloudFormation (AWS state), S3 (log bucket) (002-ipa-security-skill)
- Markdown (Claude Code skill format) — the skill is an instruction document, not executable code + Claude Code skill framework, stack skill files (input), AWS CLI (in generated Makefiles) (003-ipa-compose-skill)
- Filesystem — reads from `.claude/skills/`, `.env`, `infra/cfn/`; writes to `.claude/skills/`, `scripts/` (003-ipa-compose-skill)
- YAML (CloudFormation), Markdown (skill files) + Claude Code skill framework, AWS CLI, `aws cloudformation validate-template` (004-cognito-stack-skill)
- N/A — infrastructure-as-code artifacts only (004-cognito-stack-skill)
- YAML (CloudFormation templates), Markdown (skill files) + Claude Code skill framework, AWS CLI (006-ecr-stack-skill)
- Markdown (Claude Code skill format) — no executable code + Claude Code skill framework, `.env` configuration, stack skills (`ipa-stack-*`) (007-simplify-compose)
- Filesystem — reads from `.claude/skills/`, `.env`, `infra/cfn/`; writes to `scripts/` (007-simplify-compose)
- Markdown (Claude Code skill format) — no executable code + Claude Code skill framework, AWS CLI, GNU Make (008-ipa-deploy-skill)
- N/A — reads `.env` and `scripts/*.mk`; does not write to any files (008-ipa-deploy-skill)
- Markdown (Claude Code skill format) — no executable code + Claude Code skill framework, AWS CLI, GNU Make (009-compose-stacks)
- Filesystem — reads from `.claude/skills/`, `.env`, `infra/cfn/`; writes to `.claude/skills/ipa-compose/`, `scripts/` (009-compose-stacks)
- Markdown (Claude Code skill format) + None — Claude Code is the runtime (001-ipa-init-skill)
- Python 3.12 (backend), TypeScript 5.9 (frontend — no changes needed) + FastAPI, PynamoDB, boto3 (Bedrock + SQS), Pydantic, uvicorn (011-passenger-jobs)
- DynamoDB (`app_dev_jobs` table — already deployed, `app_dev_passengers` table — existing) (011-passenger-jobs)
- YAML (CloudFormation templates), Markdown (skill files, CLAUDE.md) + AWS CloudFormation, AWS CLI, GNU Make (012-tier-stack-consolidation)
- Python 3.12 + FastAPI >=0.115, boto3 >=1.42 (Bedrock runtime), Pydantic (request validation) (013-sse-inference-routes)
- N/A (stateless — no database persistence) (013-sse-inference-routes)
- YAML (CloudFormation templates), Markdown (Claude Code skill files) — no executable code + Claude Code skill framework, AWS CLI, GNU Make (014-ipa-codepipeline)
- Markdown (Claude Code skill format) — no executable code + Claude Code skill framework (015-compose-codepipeline)

## Project Structure

```text
infra/cfn/
  frontend/frontend.yml    # Consolidated: S3 + CloudFront + OAC
  backend/backend.yml      # Consolidated: Lambda + API GW v2 + DynamoDB
  queue/queue.yml          # Consolidated: SQS + DLQ + worker Lambda + ESM + DynamoDB
  cognito/cognito.yml      # Prepare stack (unchanged)
  ecr/ecr.yml              # Prepare stack (unchanged)
.claude/skills/
  ipa-stack-frontend/      # Stack skill for frontend tier
  ipa-stack-backend/       # Stack skill for backend tier
  ipa-stack-queue/         # Stack skill for queue tier
app-lib/                   # Python backend library
web-client/                # React frontend SPA
scripts/                   # Generated Makefiles (deploy.mk, prepare.mk, etc.)
```

## Commands

# Add commands for Markdown (Claude Code skill format)

## Code Style

Markdown (Claude Code skill format): Follow standard conventions

- Feature isolation in app-lib uses Orchestration-Only Composition — see `app-lib/src/app_lib/features/CLAUDE.md`

## Recent Changes
- 015-compose-codepipeline: Integrated codecommit + codepipeline as composable prepare stacks in /ipa-compose. Deprecated standalone /ipa-codepipeline process skill. Added Compose Config prompting, env.mk pipeline target, MAKEFILE_TEMPLATES.md codepipeline notes.
- 014-ipa-codepipeline: Added YAML (CloudFormation templates), Markdown (Claude Code skill files) — no executable code + Claude Code skill framework, AWS CLI, GNU Make
- 013-sse-inference-routes: Added Python 3.12 + FastAPI >=0.115, boto3 >=1.42 (Bedrock runtime), Pydantic (request validation)
- 012-tier-stack-consolidation: Consolidated 10 per-service CFN stacks into 3 tier-based stacks (frontend, backend, queue). Removed add-stacks/add-pattern compose modes. Updated MAKEFILE_TEMPLATES.md for consolidated stack names.


## Commit Messages

Every commit message MUST use [Conventional Commits](https://www.conventionalcommits.org/) format. This is not a style preference — the format is the input to two automated outputs:

1. **Version derivation.** The next release version is computed from commit history, not read from a file. A `fix:` commit produces a patch bump, `feat:` a minor bump; a commit that matches no conventional type produces **no bump at all**.
2. **Published release notes.** The GitHub Release body is generated from these messages. A non-conventional commit appears in **no** release-notes section and is invisible to anyone reading the release.

So a commit written as `Update: modify 7 file(s)` is silently skipped by both — the work ships, but nothing records that it did. Write `fix(app-lib): ...` instead.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | When to use | Release notes section |
|------|-------------|-----------------------|
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

### Scopes (optional)

Use a scope when the change is clearly limited to one area:

- `ipa` — IPA skills framework (`.claude/skills/`, `scripts/`)
- `app-lib` — Python backend library (`app-lib/`)
- `web-client` — React frontend (`web-client/`)
- `docs` — Documentation site (`docs/`)
- `infra` — CloudFormation templates (`infra/cfn/`)

### Rules

- Description: imperative mood, lowercase start, no trailing period, max 72 characters
- Body: wrap at 72 characters, explain WHY not WHAT
- Breaking changes: append `!` after type/scope — but only for the **public interface**. See
  [Versioning](#versioning-what-each-type-derives) below, which is the authoritative rule
- Multi-scope changes: omit scope — `feat: add passenger job queue`

### Examples

```
feat(ipa): add logs stack for centralized S3 log bucket
fix(web-client): resolve OIDC token refresh race condition
docs: update releasing guide for trunk-based workflow
ci: add manual tag-and-release trigger
refactor(app-lib): extract AbstractDataService from passenger service
chore: bump FastAPI to 0.115.12
build(infra): consolidate backend tier template parameters
```

### Versioning: what each type derives

The type you choose **is** the version bump. Measured against this repository's `cliff.toml`:

| Subject | From `v0.2.1` derives | Bump |
|---|---|---|
| `feat:` | `v0.3.0` | minor |
| `fix:` `docs:` `refactor:` `perf:` `ci:` `build:` `revert:` | `v0.2.2` | patch |
| `style:` `test:` `chore:` `Update:` | `v0.2.1` | **none** |
| any bumping type with `!` | `v0.3.0` | minor pre-1.0, **major** from 1.0 on |

Three consequences that are easy to get wrong:

- **`chore!:` derives nothing.** `chore` is `skip = true`, so the `!` is swallowed — no bump *and*
  no release-notes entry. A breaking change filed as `chore!:` is completely invisible. Never put
  `!` on a skipped type; pick a type that bumps.
- **A `BREAKING CHANGE:` footer bumps on its own**, with no `!` in the subject. The two are
  independent triggers, so a commit carrying only the footer still bumps. Use both or neither.
- **Pre-1.0, `!` turns a patch into a minor.** `refactor!:` derives `v0.3.0` where `refactor:`
  derives `v0.2.2`. From 1.0 onward the same `!` derives a *major*, and such a release is refused
  unless `CONFIRM_VERSION` names the exact derived version — so 1.0.0 cannot be reached by accident.

### What counts as breaking: public vs internal interface

SemVer's contract covers the **public interface** — what a consumer of IPA touches. Reserve `!`
for changes to that surface. Changing how *this repository* is maintained is not a breaking change,
however large the diff.

**Public interface — `!` applies when you break it:**

- **Skill contracts** — `.claude/skills/ipa-*`: skill names, their arguments and prompts, and the
  files they generate
- **CloudFormation templates** — `infra/cfn/**`: parameter names, outputs, and resource logical IDs
  (a rename forces stack replacement or breaks cross-stack wiring)
- **Generated artifacts** — `scripts/*.mk` target names, `INSTALL-RUNBOOK.md`,
  `SECURITY-DISPOSITION.md`, and the `.env` keys they read. These must work **without IPA**, so a
  renamed target breaks a customer even though nothing in this repo consumes it
- **`internal/release/templates/`** — the portable release standard, copied into customer projects.
  Its name is misleading: it is public interface despite living under `internal/`
- **`app-lib/` HTTP surface** — route paths, request and response shapes
- **`web-client/`** — runtime config contract (`window.__CONFIG__`) and auth flow

**Internal — `!` does not apply, however sweeping the change:**

- `.gitlab-ci.yml`, `.github/workflows/**`, `infra/scripts/**` — the framework's own build and
  release tooling
- `internal/**` *except* `templates/`
- `docs/docs/developer-docs/internal/**`, `CLAUDE.md`, `openspec/`, `.context/`, `.ash/`
- The release procedure itself, and anything only a maintainer of this repo performs

**Worked example.** Retiring the committed changelog rewrote the entire release path — eight CI
jobs to three, five scripts to one, ~1,660 lines deleted. It was committed as `refactor(ipa):`
with **no** `!`, deriving a patch, because no skill, template, generated artifact, or deployed
behaviour changed. It was first written as `refactor(ipa)!:`, which derived `v0.3.0` and overstated
the change; the `!` and its footer were removed. When unsure, ask: *would a consumer who never
releases this project notice?* If no, no `!`.

### Release Commits

**There is no release commit.** Cutting a release creates an annotated tag and a forge Release object and writes nothing to the repository, so nothing in commit history marks a release and no commit subject is reserved.

To find releases, read the tags:

```bash
git tag --list                              # every released version
git tag -l --format='%(contents)' v0.2.1    # that version's release notes
```

Release notes are generated from commit history at release time and stored on the tag annotation and the Release object. There is no committed changelog, which is why the format above is the only record of what a release contains — a commit that matches no conventional type is invisible, with no artifact in which anyone would notice.

<!-- MANUAL ADDITIONS START -->

## Security Scanning

- ASH (Automated Security Helper) config lives at `.ash/ash.yaml` — add SAST suppressions there with `rule_id`, `path`, and `reason`
- Every suppression must include a `reason` explaining why it is safe to suppress

<!-- MANUAL ADDITIONS END -->
