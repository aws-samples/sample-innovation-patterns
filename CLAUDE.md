# innovation-patterns Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-26

## Active Technologies
- Markdown (Claude Code skill format) + Claude Code skill framework, `uv run deploy cfn` utility (from utils-uv-commands feature), AWS CLI (fallback) (002-ipa-security-skill)
- `.env` (local config file), CloudFormation (AWS state), S3 (log bucket) (002-ipa-security-skill)
- Markdown (Claude Code skill format) — the skill is an instruction document, not executable code + Claude Code skill framework, pattern/stack skill files (input), execution layer `utils/` (referenced in generated Makefiles) (003-ipa-compose-skill)
- Filesystem — reads from `.claude/skills/`, `.env`, `infra/cfn/`; writes to `.claude/skills/`, `scripts/`, `docs/infra/` (003-ipa-compose-skill)

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
- 003-ipa-compose-skill: Added Markdown (Claude Code skill format) — the skill is an instruction document, not executable code + Claude Code skill framework, pattern/stack skill files (input), execution layer `utils/` (referenced in generated Makefiles)
- 002-ipa-security-skill: Added Markdown (Claude Code skill format) + Claude Code skill framework, `uv run deploy cfn` utility (from utils-uv-commands feature), AWS CLI (fallback)

- 001-ipa-init-skill: Added Markdown (Claude Code skill format) + None — Claude Code is the runtime

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
