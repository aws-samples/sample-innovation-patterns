# innovation-patterns Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-10

## Active Technologies
- Markdown (Claude Code skill format) + Claude Code skill framework, AWS CLI (002-ipa-security-skill)
- `.env` (local config file), CloudFormation (AWS state), S3 (log bucket) (002-ipa-security-skill)
- Markdown (Claude Code skill format) — the skill is an instruction document, not executable code + Claude Code skill framework, pattern/stack skill files (input), AWS CLI (in generated Makefiles) (003-ipa-compose-skill)
- Filesystem — reads from `.claude/skills/`, `.env`, `infra/cfn/`; writes to `.claude/skills/`, `scripts/` (003-ipa-compose-skill)
- YAML (CloudFormation), Markdown (skill files) + Claude Code skill framework, AWS CLI, `aws cloudformation validate-template` (004-cognito-stack-skill)
- N/A — infrastructure-as-code artifacts only (004-cognito-stack-skill)
- YAML (CloudFormation templates), Markdown (skill files) + Claude Code skill framework, AWS CLI (006-ecr-stack-skill)
- Markdown (Claude Code skill format) — no executable code + Claude Code skill framework, `.env` configuration, stack skills (`ipa.stack.*`) (007-simplify-compose)
- Filesystem — reads from `.claude/skills/`, `.env`, `infra/cfn/`; writes to `scripts/` (007-simplify-compose)
- Markdown (Claude Code skill format) — no executable code + Claude Code skill framework, AWS CLI, GNU Make (008-ipa-deploy-skill)
- N/A — reads `.env` and `scripts/*.mk`; does not write to any files (008-ipa-deploy-skill)
- Markdown (Claude Code skill format) — no executable code + Claude Code skill framework, AWS CLI, GNU Make (009-compose-stacks)
- Filesystem — reads from `.claude/skills/`, `.env`, `infra/cfn/`, `patterns/`; writes to `.claude/skills/ipa.compose/`, `scripts/` (009-compose-stacks)
- Markdown (Claude Code skill format) + None — Claude Code is the runtime (001-ipa-init-skill)
- Python 3.12 (backend), TypeScript 5.9 (frontend — no changes needed) + FastAPI, PynamoDB, boto3 (Bedrock + SQS), Pydantic, uvicorn (011-passenger-jobs)
- DynamoDB (`app_dev_jobs` table — already deployed, `app_dev_passengers` table — existing) (011-passenger-jobs)
- YAML (CloudFormation templates), Markdown (skill files, CLAUDE.md) + AWS CloudFormation, AWS CLI, GNU Make (012-tier-stack-consolidation)
- Python 3.12 + FastAPI >=0.115, boto3 >=1.42 (Bedrock runtime), Pydantic (request validation) (013-sse-inference-routes)
- N/A (stateless — no database persistence) (013-sse-inference-routes)
- YAML (CloudFormation templates), Markdown (Claude Code skill files) — no executable code + Claude Code skill framework, AWS CLI, GNU Make (014-ipa-codepipeline)

## Project Structure

```text
infra/cfn/
  frontend/frontend.yml    # Consolidated: S3 + CloudFront + OAC
  backend/backend.yml      # Consolidated: Lambda + API GW v2 + DynamoDB + CloudWatch
  queue/queue.yml          # Consolidated: SQS + DLQ + worker Lambda + ESM + DynamoDB + CloudWatch
  cognito/cognito.yml      # Prepare stack (unchanged)
  ecr/ecr.yml              # Prepare stack (unchanged)
.claude/skills/
  ipa.stack.frontend/      # Stack skill for frontend tier
  ipa.stack.backend/       # Stack skill for backend tier
  ipa.stack.queue/         # Stack skill for queue tier
  ipa.compose/patterns/    # Pattern definitions (react-rest-lambda, sqs-lambda)
app-lib/                   # Python backend library
web-client/                # React frontend SPA
scripts/                   # Generated Makefiles (deploy.mk, prepare.mk, etc.)
```

## Commands

# Add commands for Markdown (Claude Code skill format)

## Code Style

Markdown (Claude Code skill format): Follow standard conventions

## Recent Changes
- 014-ipa-codepipeline: Added YAML (CloudFormation templates), Markdown (Claude Code skill files) — no executable code + Claude Code skill framework, AWS CLI, GNU Make
- 013-sse-inference-routes: Added Python 3.12 + FastAPI >=0.115, boto3 >=1.42 (Bedrock runtime), Pydantic (request validation)
- 012-tier-stack-consolidation: Consolidated 10 per-service CFN stacks into 3 tier-based stacks (frontend, backend, queue). Removed add-stacks/add-pattern compose modes. Updated pattern definitions and MAKEFILE_TEMPLATES.md for consolidated stack names.


<!-- MANUAL ADDITIONS START -->

## Security Scanning

- ASH (Automated Security Helper) config lives at `.ash/ash.yaml` — add SAST suppressions there with `rule_id`, `path`, and `reason`
- Every suppression must include a `reason` explaining why it is safe to suppress

<!-- MANUAL ADDITIONS END -->
