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

Use [Conventional Commits](https://www.conventionalcommits.org/) format for all commit messages.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

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
- Breaking changes: append `!` after type/scope — `feat(app-lib)!: change response format`
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

### Release Commits

When preparing a release, use:
```
chore: release v0.2.0
```

<!-- MANUAL ADDITIONS START -->

## Security Scanning

- ASH (Automated Security Helper) config lives at `.ash/ash.yaml` — add SAST suppressions there with `rule_id`, `path`, and `reason`
- Every suppression must include a `reason` explaining why it is safe to suppress

<!-- MANUAL ADDITIONS END -->
