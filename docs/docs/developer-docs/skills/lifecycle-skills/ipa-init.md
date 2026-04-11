---
title: /ipa.init
sidebar_position: 2
---

# /ipa.init

Interactively configure a project's `.env` file with the IPA-managed variables required by all downstream skills.

## Invocation

    /ipa.init

## Parameters

`/ipa.init` prompts for all parameters interactively. No arguments are passed at invocation.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_PROFILE` | No | *(skipped)* | AWS CLI named profile. Omitted from `.env` if skipped. |
| `AWS_REGION` | Yes | `us-east-1` | AWS deployment region |
| `AWS_ACCOUNT_ID` | Yes | *(auto-detected)* | 12-digit account ID, detected via `aws sts get-caller-identity` |
| `APP_NAMESPACE` | Yes | `app` | 1-12 character project prefix (lowercase alphanumeric) |
| `APP_ENV` | Yes | `dev` | Environment label (`dev`, `stage`, `prod`) |
| `APP_CODE_AGENT` | Auto | `claude-code` | Fixed value, not prompted |
| `APP_IAC` | Auto | `cloudformation` | Fixed value, not prompted |

## What It Does

1. **First-time initialization** — Presents a single batched prompt for all configurable variables with sensible defaults. Validates each input against strict regex patterns. Writes the `.env` file and generates a `.env.example` template (never committed to version control).

2. **Re-initialization** — Detects an existing `.env` file and enters selective-update mode. Displays current values and prompts only for variables the user wants to change. Warns before overwriting existing values.

3. **Security chain** — On first run, if the security stack has not been provisioned, automatically chains to `/ipa.security` after `.env` is written.

## Outputs

| Artifact | Path | Description |
|----------|------|-------------|
| Environment file | `.env` | Project configuration consumed by all IPA skills |
| Example template | `.env.example` | Sanitized template showing required variables |

## Examples

**Initialize a new project:**

    /ipa.init

Respond to the prompts with your AWS profile, region, namespace (`myapp`), and environment (`dev`). The skill writes `.env` and proceeds to `/ipa.security`.

**Update an existing configuration:**

    /ipa.init

The skill detects the existing `.env`, displays current values, and prompts for changes.

## Related Skills

- [/ipa.security](./ipa-security.md) — Automatically invoked after first-time initialization
- [/ipa.compose](./ipa-compose.md) — Reads `.env` variables written by this skill
