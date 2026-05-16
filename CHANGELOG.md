# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.6]

### Changed

- **web-client build tooling** — replaced `@vitejs/plugin-react-swc` with `@vitejs/plugin-react` (Babel-based) to eliminate platform-specific `@swc/core` binaries from the dependency tree. This fixes CodeBuild `npm ci` failures when `package-lock.json` is generated on macOS but CI runs on Linux. No application code changes; build, tests, and dev server verified.

### Fixed

- **web-client cross-platform lockfile** — regenerated `web-client/package-lock.json` to include both Linux x64 and macOS arm64 entries for native packages (`@rollup/rollup-*`, `@esbuild/*`, `@tailwindcss/oxide-*`, `lightningcss-*`). The prior swc fix only addressed swc binaries; CodeBuild `npm ci` was still failing on missing Linux variants for tailwind v4, esbuild, rollup, and lightningcss. Verified with `npm ci --os=linux --cpu=x64` and local `npm run build`.

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
