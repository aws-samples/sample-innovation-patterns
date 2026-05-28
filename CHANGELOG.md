# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.7]

### Added
- **Terraform as a first-class IaC engine** — `APP_IAC=terraform` in `.env` switches `/ipa-compose` to generate `terraform init/apply/destroy` Makefile targets instead of `aws cloudformation deploy`. Eight idiomatic HCL root modules under `infra/tf/` (backend, frontend, queue, cognito, ecr, logs, codecommit, codepipeline) mirror the existing CFN tier/prepare stacks. Terraform state backend (S3 + DynamoDB) is bootstrapped via a new CFN-deployed prepare stack (`infra/cfn/tfstate/tfstate.yml` + `/ipa-stack-tfstate` skill) — the chicken-and-egg exception that stays CFN even in full-TF mode. `/ipa-init` promotes `APP_IAC` from auto-set to a 5th prompted question. `/ipa-compose` SKILL.md adds Step 6.0 to detect IaC mode; `MAKEFILE_TEMPLATES.md` gains a complete Terraform Mode Templates section covering deploy.mk, prepare.mk, env.mk (uses `terraform output -raw`), and a `terraform validate` test target. Each `ipa-stack-*` SKILL.md now documents its parallel TF module (variables, outputs, remote-state references). Deploy→deploy wiring (e.g., queue→backend) uses subshell `terraform output` calls; prepare→deploy wiring uses `terraform_remote_state` data sources embedded in the consuming module's HCL.
- **`/ipa-init` bootstraps the Terraform state backend inline** — when the builder selects `APP_IAC=terraform`, init's Step 4.5 deploys `infra/cfn/tfstate/tfstate.yml` and writes `TF_STATE_BUCKET` / `TF_STATE_LOCK_TABLE` directly to `.env` after the main config write. Collapses the previously required init → compose → prepare-tfstate → env.mk cycle into one step — the project is deploy-ready when init returns. Re-runs are safe via `--no-fail-on-empty-changeset`. The `prepare-tfstate` target in `prepare.mk` plus `update-env-tfstate` in `env.mk` remain as the idempotent fallback path for CI/CD or environments where credentials are unavailable at init time.
- **Re-init guardrail for `APP_IAC` engine switching** — when re-running `/ipa-init` flips `APP_IAC` between `cloudformation` and `terraform`, init now displays a danger warning explaining that resources deployed by the previous engine are invisible to the new one (orphaned resources, name collisions, lost `/ipa-destroy` access). Builder must explicitly confirm via `AskUserQuestion`; the recommended option is "Cancel — keep the existing engine." Switching to `terraform` triggers Step 4.5 inline state-backend bootstrap.

### Changed
- N/A

### Removed
- **CloudWatch observability from backend and queue tier stacks** — removed dashboards, metric filters, alarms, the `AlarmSnsTopicArn` parameter, and the `cloudwatch:PutMetricData` IAM policy from `infra/cfn/backend/backend.yml` and `infra/cfn/queue/queue.yml`. The `cloudwatch-metrics` IAM policy conflicted with the centralized security stack's restricted IAM permissions, blocking deploy. Log groups (`LambdaLogGroup`, `ApiGatewayLogGroup`, `WorkerLogGroup`) and API Gateway access logging are retained — those are operational, not observability-optional. The `app-lib` `observability.py` module is retained and degrades gracefully (already wraps `put_metric_data` in try/except). Observability will be re-introduced later as a dedicated stack with its own scoped IAM permissions. Skill files, agent context (CLAUDE.md), and stacks documentation updated to match.

### Fixed
- **`/ipa-compose` deploy→deploy wiring** — `MAKEFILE_TEMPLATES.md` now splits deploy.mk wiring rules by source-stack lifecycle. Prepare-source wiring continues to read from `.env` via `$(VAR)`; deploy-source wiring captures values via `$(eval ... describe-stacks ...)` at the top of the target body, stored as `{VAR}_LIVE`. Make parses `-include .env` once at process startup, so values that env.mk writes to `.env` mid-run are invisible to subsequent targets in the same `make deploy` invocation. The previous single-rule template produced an empty `SqsSendQueueArns` for `deploy-backend`, causing `LambdaExecutionRole` `CREATE_FAILED` on IAM ("Resource must be in ARN format or '*'"). The `ipa-stack-backend` skill now flags `SqsQueueUrl`/`SqsSendQueueArns` as same-lifecycle wiring per Case B.
- **CodePipeline buildspec hardening** — upgraded CodeBuild image to `aws/codebuild/standard:8.0` (Node 20+), now installs `uv` during install phase, and runs `uv sync` plus a frontend rebuild in PreBuild so the OpenAPI codegen pipeline and `web-client/dist` artifact are present in CI environments where they were previously missing. PostDeploy gained an `ensure-frontend-dist` step that rebuilds the SPA if the cross-stage artifact is absent.
- **CodeBuild buildspec YAML parsing** — replaced bare `{ … }` shell expressions in inline buildspec command scalars with `- |` block scalars; YAML was interpreting the braces as flow mappings and failing to parse the pipeline definition. Documented the pitfall in the `/ipa-codepipeline` skill.
- **env.mk two-invocation bootstrap inside CodePipeline** — applied the same prelude pattern used by local `make deploy` to the inline buildspec so each stage populates `.env` from live stack outputs before the main target runs. Eliminates stale or empty values when CodeBuild's environment is the only source of truth.
- **Passengers DynamoDB table alignment** — renamed table to use underscores (`app_dev_passengers`) and re-aligned the CFN hash key with the PynamoDB model. Drift between template and model was causing runtime `ValidationException` on `GetItem`/`PutItem`. `uv run` for the load-data target now passes `--all-extras` so optional dependencies resolve in CI.
- **Terraform/CloudFormation parity** — brought `infra/tf/*` modules to feature parity with their CFN counterparts after the consolidation, fixed a naming-contract drift between engines, and adjusted the Cognito module to use `username` consistently. `terraform output -raw` was leaking `Warning: No outputs found` to stdout and corrupting `.env`; env.mk now uses `terraform output -json | jq` for safe capture.
- **API Gateway v2 CORS preflight under JWT** — added an explicit `OPTIONS /{proxy+}` route with `AuthorizationType=NONE` so browser preflights reach the Lambda instead of being rejected by the JWT authorizer at the `$default` route. Documented the pattern in the `ipa-stack-backend` skill (Terraform + CFN).

### Documentation

- New `developer-docs/infra/terraform.md` covering the dual-engine model, state-backend bootstrap, and engine-switch guardrail.

## [0.1.6] - 2026-05-18

### Added

- **Conventional Commits convention** — adopted [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages, with type/scope/breaking-change rules documented in `CLAUDE.md` and a public reference at `developer-docs/contributing/commit-messages.md`.
- **CHANGELOG automation via git-cliff** — added `cliff.toml` mapping conventional commit types to Keep-a-Changelog sections, plus a `release-changelog` Make target that regenerates `CHANGELOG.md` from commit history. Run `make -f scripts/util/release.mk release-prep VERSION=X.Y.Z` to stamp VERSION and produce a CHANGELOG draft in one step.
- **Manual `Tag & Release` trigger** — GitLab CI release job is now a manual play button on `main` pipelines instead of auto-firing on every VERSION-bump merge. The builder decides when to release; `release-check.sh` still validates VERSION ↔ tag at runtime.

### Changed

- **Trunk-based development on `main`** — the project moves from the develop → main merge-based release flow to trunk-based development on `main`. Daily work lands on `main` directly or via short-lived feature branches. Eliminates the SHA-reconciliation merges that were required to keep `develop` and `main` aligned.
- **`scripts/env.mk` is now the canonical bridge between live CloudFormation stack outputs and the Make system.** Every consumer (`deploy.mk`, `post-deploy.mk`, local dev server) reads values from `.env`; only env.mk calls `aws cloudformation describe-stacks`. CodeBuild stages run env.mk as a prelude to populate `.env` before each stage's main target. Stack outputs are no longer baked into CodeBuild EnvironmentVariables, where they could go stale and silently override live values via Make's environment-precedence rule. Generated Makefiles drop all inline `$(eval ... describe-stacks ...)` from deploy and post-deploy targets — only env.mk and prepare.mk (the bootstrap) keep them.
- **web-client build tooling** — replaced `@vitejs/plugin-react-swc` with `@vitejs/plugin-react` (Babel-based) to eliminate platform-specific `@swc/core` binaries from the dependency tree. This fixes CodeBuild `npm ci` failures when `package-lock.json` is generated on macOS but CI runs on Linux. No application code changes; build, tests, and dev server verified.

### Fixed

- **web-client cross-platform lockfile** — regenerated `web-client/package-lock.json` to include both Linux x64 and macOS arm64 entries for native packages (`@rollup/rollup-*`, `@esbuild/*`, `@tailwindcss/oxide-*`, `lightningcss-*`). The prior swc fix only addressed swc binaries; CodeBuild `npm ci` was still failing on missing Linux variants for tailwind v4, esbuild, rollup, and lightningcss. Verified with `npm ci --os=linux --cpu=x64` and local `npm run build`.
- **Innovation Builder Security stack** — added `cloudwatch:*` to the Infrastructure allow block of `InnovationBuilderPolicy`. Tier stacks declaring `AWS::CloudWatch::Alarm` or `AWS::CloudWatch::Dashboard` (queue, backend) previously failed during deploy with `cloudwatch:PutDashboard`/`cloudwatch:PutMetricAlarm` AccessDenied. The destructive subset (`DeleteAlarms`, `DeleteDashboards`, `DisableAlarmActions`) remains denied by the existing `SecureLoggingConfigs` deny block in both the boundary and identity policy.
- **`update-cognito-callback` parameter drift** — the post-deploy step now reads `COGNITO_DOMAIN_PREFIX` from `.env` (populated by `env.mk` from the live `CognitoDomain` stack output) instead of recomputing it as `$(APP_NAMESPACE)-$(APP_ENV)-$(APP_ACCOUNT_HASH)`. The recomputed value could differ from the deployed parameter (different `AWS_ACCOUNT_ID`, different `.env` across hosts, etc.), which CFN treated as a property change → REPLACE on `AWS::Cognito::UserPoolDomain` → live domain destroyed mid-update. Reading the deployed value eliminates the drift.
- **Frontend deploy `LogBucketDomainName` empty in CodeBuild** — `deploy-frontend` previously read `$(LOG_BUCKET_NAME)` directly from `.env`, but `.env` did not exist in CodeBuild and the variable was not in the CodeBuild EnvironmentVariables. The empty value produced `LogBucketDomainName=.s3.amazonaws.com`, causing `WebBucket` to fail with "The specified bucket is not valid." Now generalized via the env.mk refactor — every deploy stage's prelude populates `.env` from live stack state.

## [0.1.5] - 2026-05-13

### Added

- N/A

### Fixed

- **Release pipeline** — combined `auto-tag` and `github-release` into a single `auto-tag-and-release` job. Separate jobs were unreliable because `CI_JOB_TOKEN`-authenticated tag pushes do not trigger follow-up pipelines, so the tag-driven release job never fired. Trade-off: manually pushed tags no longer trigger a GitHub release.

## [0.1.4] - 2026-05-13

### Added

- **`/ipa-stack-logs`** — new prepare-lifecycle stack for a centralized S3 log bucket (CloudFront, S3 access, VPC flow logs). Composed via `/ipa-compose` and auto-included as a transitive dependency when a downstream stack wires `LogBucketName`. Generates `update-env-logs` env.mk target and a `prepare.mk` teardown note for non-empty buckets.

### Changed

- **`/ipa-security`** — log bucket extracted from the security stack into the new `/ipa-stack-logs` prepare stack. `/ipa-security` now provisions only IAM roles (one CloudFormation stack instead of two). The frontend tier's `LogBucketDomainName` parameter now sources from `logs` instead of `security`.
- **`/ipa-compose`** — recursive auto-include now resolves `logs` alongside `cognito`/`ecr`/`codecommit`. Generated deploy targets that reference `$(LOG_BUCKET_NAME)` now emit a pre-check that validates the `{ns}-{env}-logs` stack exists before deploying.

### Fixed

- **Docs site** — Docusaurus `baseUrl` now derives from `CI_PAGES_URL` so the GitLab Pages deploy tracks the project slug instead of a hardcoded path.

## [0.1.3] - 2026-05-12

### Changed

- **Compose CodePipeline** — integrated `codecommit` and `codepipeline` as composable prepare-lifecycle stacks in `/ipa-compose`. Added `## Stack Identity`, `## Wirable Parameters`, `## Compose Config`, and `## Deploy Order` to both stack skills. Compose auto-includes `codecommit` as a transitive dependency of `codepipeline`, prompts for repository name and source branch, and generates `prepare.mk` targets with full cross-stack wiring. Added `update-env-pipeline` target to env.mk generation.

### Deprecated

- **`/ipa-codepipeline`** — replaced with the standard compose+prepare flow (`/ipa-compose codepipeline` → `/ipa-prepare`). Existing deployments are compatible; re-compose to align.

## [0.1.2] - 2026-05-11

### Changed

- **Lifecycle refactor** — collapsed 5-skill lifecycle into 4-step flow: `/ipa-init` → `/ipa-compose` → `/ipa-prepare` → `/ipa-deploy`. `/ipa-security` is now embedded in `/ipa-compose` (triggered on first compose) and supports three paths: existing role ARN, managed policy, or the new Innovation Builder Stack (recommended — permissions boundary + 47-service policy + four scoped roles). `/ipa-compose` auto-runs `/ipa-init` when `.env` is missing; `/ipa-deploy` hard-gates on prepare stacks instead of auto-triggering. Split `infra/cfn/generated/security.yml` into `iam.yml` + `log-bucket.yml`.
- **Skill naming** — renamed all `ipa.*` skills to use `-` as the separator instead of `.` (e.g., `/ipa.compose` → `/ipa-compose`, `/ipa.stack.backend` → `/ipa-stack-backend`). Affects 17 skill directories, frontmatter, internal references, and all published documentation.

### Added

- **`/ipa-help`** — new diagnostic skill that reports IPA project state and suggests the next lifecycle skill to run. Read-only; does not invoke other skills.
- **Innovation Builder Security stack** — new single-template CloudFormation stack at `infra/cfn/security/innovation-builder-security.yml` consolidating the IAM policy + permissions boundary, CodeBuild role, SageMaker execution role, builder role, and EC2 builder role into one deployable artifact. Consumed as-is by `/ipa-security`; deploy this OR the per-resource templates, not both.
- **`/ipa-security` skill** — full implementation supporting three setup paths (existing role ARN, AWS managed policy, or the Innovation Builder Stack), with deploy/update/review flows, `.env` wiring for `DEPLOYMENT_ROLE_ARN`/`PERMISSIONS_BOUNDARY_ARN`, and stack drift handling.

### Removed

- **`/ipa-quickstart`** — removed; the 4-step lifecycle is the new quickstart.

## [0.1.1] - 2026-04-26

### Changed

- **Docs site** — GitHub Pages now deploys on pushes to `main` instead of release tags, matching the existing GitLab Pages trigger and avoiding the `github-pages` environment protection rule that blocks tag-based deploys.

### Fixed

- **Release pipeline** — `github-push.sh` now sets a local committer identity before amending the filtered release commit, preventing `fatal: unable to auto-detect email address` in CI.
- **Release pipeline** — after amending the release commit to strip internal-only paths, the release tag is now moved to the amended commit so GitHub's tag, `main`, and auto-generated release tarball all reference the same filtered tree.
- **Auto-tag** — rule no longer excludes `$CI_PIPELINE_SOURCE == "push"`, which was blocking the job from ever firing on a standard push-to-main. Tag existence now checked against `origin` to tolerate CI's shallow clone.

## [0.1.0] - 2026-04-26

### Added

- **IPA Skills Framework** — composable Claude Code skills for AWS infrastructure deployment
  - Lifecycle skills: `/ipa.init`, `/ipa.security`, `/ipa.compose`, `/ipa.prepare`, `/ipa.deploy`, `/ipa.destroy`
  - Authoring skills: `/ipa.author.stack`, `/ipa.author.guide`
  - CI/CD skill: `/ipa.codepipeline`
- **Tier Stacks** — consolidated CloudFormation templates for serverless applications
  - Backend tier: Lambda + API Gateway v2 + DynamoDB + CloudWatch
  - Frontend tier: S3 + CloudFront + OAC
  - Queue tier: SQS + DLQ + worker Lambda + ESM + DynamoDB + CloudWatch
- **Prepare Stacks** — one-time prerequisite infrastructure
  - Cognito User Pool with OAuth 2.0 Hosted UI
  - ECR repository for container images
- **Patterns** — composable solution templates
  - `react-rest-lambda` — full-stack serverless web application
  - `sqs-lambda` — background job processing (compose-only, layers onto base pattern)
- **Application Library (`app-lib/`)** — Python 3.12 library with FastAPI, PynamoDB, JWT auth, and feature-centric module architecture
- **Web Client (`web-client/`)** — React 19 + TypeScript SPA with RTK Query, Cognito OIDC, and OpenAPI codegen pipeline
- **Documentation Site** — Docusaurus 3 with autogenerated sidebars, Mermaid diagrams, and local-only working section
- **Security** — ASH integration in GitLab CI, least-privilege IAM, encryption by default
- **Generated Makefiles** — plain GNU Make with inline `aws` CLI calls; no runtime dependency on IPA

[Unreleased]: https://github.com/aws-samples/sample-innovation-patterns/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/aws-samples/sample-innovation-patterns/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/aws-samples/sample-innovation-patterns/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/aws-samples/sample-innovation-patterns/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/aws-samples/sample-innovation-patterns/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/aws-samples/sample-innovation-patterns/releases/tag/v0.1.0
