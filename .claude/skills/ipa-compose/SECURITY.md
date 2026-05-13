# Security Phase Reference

This document details the security configuration phase embedded in `/ipa-compose` (Step 1.5).

## When It Runs

- **First compose** (no `APP_BUILDER_ROLE_ARN` in `.env`): Prompts the builder for security path selection.
- **Re-compose** (`APP_BUILDER_ROLE_ARN` present): Skipped silently — security is already configured.

## Three Configuration Paths

| Path | What Happens | Template Used |
|------|-------------|---------------|
| A — Existing Role ARN | Builder provides pre-provisioned role ARNs | No template (roles already exist) |
| B — Managed Policy ARN | IPA creates Builder + CodeBuild roles with chosen policy | `infra/cfn/generated/iam.yml` |
| C — Innovation Builder Stack | Deploys full security stack (boundary + 47-service policy + 4 roles) | `infra/cfn/security/innovation-builder-security.yml` |

## Log Bucket

The centralized S3 log bucket is **not** part of security provisioning. It is a prepare-lifecycle stack deployed via `/ipa-prepare` (see `ipa-stack-logs`). When `/ipa-compose` detects that a composed stack has `logs` as a wiring source, the log bucket is auto-included in `prepare.mk`.

## Delegation

Compose collects the path selection and delegates to `/ipa-security` in `mode=init` with the chosen path. `/ipa-security` owns all IAM provisioning logic:

- Template selection and deployment
- Stack naming (`{namespace}-{env}-security`)
- `.env` variable writes (`APP_BUILDER_ROLE_ARN`, `APP_CODEBUILD_ROLE_ARN`)
- Error handling and recovery

## Re-Configuration

To change security configuration after initial setup, invoke `/ipa-security` directly. It detects the existing stack and offers the update flow.
