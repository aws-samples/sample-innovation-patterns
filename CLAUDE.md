# innovation-patterns Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-27

## Active Technologies
- Markdown (Claude Code skill format) + Claude Code skill framework, `uv run deploy cfn` utility (from utils-uv-commands feature), AWS CLI (fallback) (002-ipa-security-skill)
- `.env` (local config file), CloudFormation (AWS state), S3 (log bucket) (002-ipa-security-skill)
- Markdown (Claude Code skill format) — the skill is an instruction document, not executable code + Claude Code skill framework, pattern/stack skill files (input), execution layer `utils/` (referenced in generated Makefiles) (003-ipa-compose-skill)
- Filesystem — reads from `.claude/skills/`, `.env`, `infra/cfn/`; writes to `.claude/skills/`, `scripts/`, `docs/infra/` (003-ipa-compose-skill)
- YAML (CloudFormation), Markdown (skill files) + Claude Code skill framework, `uv run deploy cfn` execution layer, cfn-lin (004-cognito-stack-skill)
- N/A — infrastructure-as-code artifacts only (004-cognito-stack-skill)
- YAML (CloudFormation templates), Markdown (skill files) + Claude Code skill framework, `uv run deploy cfn` execution layer, cfn-lin (006-ecr-stack-skill)
- Markdown (Claude Code skill format) — no executable code + Claude Code skill framework, `.env` configuration, stack skills (`ipa.stack.*`) (007-simplify-compose)
- Filesystem — reads from `.claude/skills/`, `.env`, `infra/cfn/`; writes to `scripts/`, `docs/infra/` (007-simplify-compose)

- Markdown (Claude Code skill format) + None — Claude Code is the runtime (001-ipa-init-skill)

## Project Structure

```text
src/
tests/
```

## Commands

# Add commands for Markdown (Claude Code skill format)

## Code Style

Markdown (Claude Code skill format): Follow standard conventions

## Recent Changes
- 007-simplify-compose: Added Markdown (Claude Code skill format) — no executable code + Claude Code skill framework, `.env` configuration, stack skills (`ipa.stack.*`)
- 007-simplify-compose: Added Markdown (Claude Code skill format) — no executable code + Claude Code skill framework, `.env` configuration, stack skills (`ipa.stack.*`)
- 006-ecr-stack-skill: Added YAML (CloudFormation templates), Markdown (skill files) + Claude Code skill framework, `uv run deploy cfn` execution layer, cfn-lin


<!-- MANUAL ADDITIONS START -->

## Security Scanning

- ASH (Automated Security Helper) config lives at `.ash/ash.yaml` — add SAST suppressions there with `rule_id`, `path`, and `reason`
- Every suppression must include a `reason` explaining why it is safe to suppress

<!-- MANUAL ADDITIONS END -->
