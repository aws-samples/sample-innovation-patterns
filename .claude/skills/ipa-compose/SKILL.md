---
name: ipa-compose
description: "Compose a deployment from stack skills and generate executable artifacts
  (Makefiles, security disposition). Use when the user says 'compose',
  'generate deployment', or invokes /ipa-compose."
model: opus
---

# /ipa-compose — Compose Deployment from Stack Skills

This skill reads stack skills directly, composes them into a project-specific deployment configuration, and generates six executable artifacts: five Makefiles (prepare, deploy, build, post-deploy, test) and a security disposition register. It also handles first-time security provisioning via delegation to `/ipa-security`.

**Lifecycle**: `/ipa-init` → **`/ipa-compose`** → `/ipa-prepare` → `/ipa-deploy`

---

## Phase 0.5: Auto-Init Gate

Before any validation, check if `.env` exists and contains the required IPA variables
(`APP_NAMESPACE`, `APP_ENV`, `AWS_REGION`, `AWS_ACCOUNT_ID`).

- **If all present**: proceed to Phase 0.
- **If `.env` missing or any required variable absent**:
  Display: "Project not initialized. Running `/ipa-init` to configure defaults…"
  Invoke `/ipa-init` (full interactive flow — 4 questions).
  On success, resume this skill from Phase 0.
  On `/ipa-init` failure, STOP.

---

## Phase 0: Parse Intent

This phase parses the builder's input, classifies arguments, detects whether an existing composition exists, and determines the composition mode.

### Step 0.1: Classify Input Arguments

Read the arguments supplied with the `/ipa-compose` invocation. For each token:

1. Check if `ipa.stack.{token}` exists as a stack skill directory in `.claude/skills/` → classify as **stack**
2. If the token matches no stack → classify as **natural language context**

For natural language tokens, attempt to resolve to known stacks. Lean on the AI agent's language understanding:

1. **Scan stacks**: For each `ipa.stack.*` directory in `.claude/skills/`, read the SKILL.md header for the description. Check if the natural language token semantically relates to the stack name or description (e.g., "API backend" matches `backend`, "web frontend" matches `frontend`, "job processing" matches `queue`).

2. **Resolve matches**:
   - **Exactly one match**: Auto-classify. Display: "Interpreted `{natural language}` as `{matched-stack}`. Correct? (yes/no):"
   - **Multiple matches**: Present all matches and ask the builder to select.
   - **No match**: Ask the builder to clarify: "Could not resolve `{natural language}` to a known stack. Available stacks: {list}."

Store the classified tokens: list of identified stack tier names and any unresolved natural language.

---

### Step 0.2: Detect Existing Composition

Check if `scripts/deploy.mk` exists:

- **If exists**: An existing composition is present. Read the first 5 lines and look for the header comment `# Deploy targets for {name}`.
  - If the header is missing or does not match the expected format, set a flag: `manual_edit_detected = true`.
  - Proceed to Step 0.3 with `existing_composition = true`.
- **If does not exist**: No existing composition. Set `existing_composition = false`.

---

### Step 0.3: Determine Composition Mode

Using the classified arguments (Step 0.1) and existing composition state (Step 0.2), determine the mode:

| deploy.mk exists? | Args contain stack(s)? | Mode |
|---|---|---|
| No | Yes | **Fresh compose** — proceed to Phase 1 with identified stack(s) |
| No | No | **Stack discovery** — proceed to Phase 1 Step 2 |
| Yes | Yes | **Fresh compose (overwrite)** — proceed to Phase 1 with identified stack(s) |
| Yes | No | **Idempotent refresh** — proceed to Step 0.3a, then Phase 1 |

---

### Step 0.3a: Extract Stack Names from deploy.mk (Idempotent Refresh Only)

Read `scripts/deploy.mk` header to determine which stack(s) were previously composed:

1. Match `# Deploy targets for {name}` in the first 5 lines.
   - Extract the stack tier name(s). If the header contains `+`, multiple stacks were composed (e.g., `backend + frontend + queue`).
   - If `manual_edit_detected` is true:
     - Warn: "deploy.mk appears to have been manually edited. Re-composing will overwrite all manual changes. Proceed? (yes to overwrite, no to cancel):"
     - If declined: exit with "Composition cancelled. No files were written."

2. Use the extracted stack name(s) as input for Phase 1 (same as fresh compose).

---

## Phase 1: Validate

### Step 1: Pre-Flight Checks

#### 1.1 Verify .env Prerequisites

Read `.env` at the project root. Verify these variables exist and are non-empty:

| Variable | Written By |
|----------|------------|
| `APP_NAMESPACE` | `/ipa-init` |
| `APP_ENV` | `/ipa-init` |
| `AWS_REGION` | `/ipa-init` |
| `AWS_ACCOUNT_ID` | `/ipa-init` |
| `AWS_PROFILE` | `/ipa-init` |

Run validation procedure V1 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

Store all variable values for use in subsequent steps.

---

### Step 1.5: Security Configuration

Check if `APP_BUILDER_ROLE_ARN` is present in `.env`:

- **Present**: Security already configured. Skip silently. Proceed to Step 2.
- **Absent**: Prompt the builder (AskUserQuestion) with three choices:

  **Question**: "How should IPA configure security infrastructure?"
  **Header**: "Security"
  **Options**:

  A) **Existing Role ARN** — "I already have builder/CodeBuild roles provisioned"
  B) **Managed Policy ARN** — "IPA creates roles with my chosen managed policy"
  C) **Innovation Builder Stack (Recommended)** — "Deploy IPA's pre-authored security stack (permissions boundary + 47-service policy + builder/CodeBuild/SageMaker/EC2 roles)"

  Delegate to `/ipa-security` with `mode=init` and `path={A|B|C}`, passing the builder's selection. On success, `APP_BUILDER_ROLE_ARN` and `APP_CODEBUILD_ROLE_ARN` are written to `.env`. Proceed to Step 2.

  On `/ipa-security` failure, STOP.

---

### Step 2: Stack Discovery

Scan `.claude/skills/` for directories matching `ipa.stack.*`. For each match, read `SKILL.md` and extract the `## Stack Identity` table to get the Tier and Lifecycle.

**If zero stacks found**: STOP — "No stack skills found in `.claude/skills/`. Author a stack skill (e.g., `ipa-stack-backend`) before running `/ipa-compose`."

**If exactly one stack found**: Auto-select it. Display: "Found one stack: **{tier}** — {description}. Proceeding with this stack."

**If multiple stacks found**: Display a numbered selection menu:

```
Available stacks:

  1. {tier1} ({lifecycle1}) — {description1}
  2. {tier2} ({lifecycle2}) — {description2}
  ...

Select stacks to compose (enter numbers, comma-separated):
```

Store the selected stack tier name(s).

---

### Step 3: Read Stack Skills and Derive Composition

For each selected stack, read `.claude/skills/ipa.stack.{tier}/SKILL.md` and extract:

| Section | Extract | Used For |
|---------|---------|----------|
| Stack Identity | Template path, suffix, capabilities, lifecycle, tier | deploy.mk targets, stack naming |
| Parameters | Parameter name list, defaults | Wiring validation, `--parameter-overrides` |
| Feature Flags | Flag names, defaults, conditions | Parameter override validation |
| Wirable Parameters | Parameter, source stack, source output, notes | Wiring map derivation |
| Outputs | Output name list | Wiring validation, `$(eval)` calls |
| Build Requirements (optional) | Type, Suffix, Dockerfile path | build.mk targets |
| Deploy Order (optional) | Ordering constraints | Deploy target prerequisites |
| Compose Config (optional) | Parameter overrides | `--parameter-overrides` entries |

**Consolidated stack skills**: The primary solution stack skills are `ipa-stack-frontend`, `ipa-stack-backend`, and `ipa-stack-queue`. Each corresponds to a single tier template in `infra/cfn/{tier}/{tier}.yml`. Prepare stack skills (`ipa-stack-cognito`, `ipa-stack-ecr`) are one-time prerequisites.

#### 3.1 Auto-Include Prepare Dependencies

For each selected stack, read its `## Wirable Parameters` section. Every **Source Stack** column value that is not already in the selected set must be auto-included. Recursively resolve until no new stacks are added.

When any selected stack's Wirable Parameters has Source Stack = `logs`, auto-include `logs` via the same recursive resolution as cognito/ecr/codecommit.

Display: "Auto-including prepare stacks: {list of auto-included tier names}"

#### 3.1.5 Prompt for Compose Config Values

For each stack in the composition that has a `## Compose Config` section with `Prompt` values:

1. Read the Compose Config table.
2. For each row with a Prompt and a Default, use AskUserQuestion to present the default as the recommended option, with "Other" available for custom input.
3. Validate input against the Validation regex (if specified).
4. Store the resolved values in a `compose_config` map keyed by `{stack}.{parameter}`.
5. These values are passed as `--parameter-overrides` in the generated prepare.mk targets.

**Special wiring rule for codepipeline + codecommit**: When `codepipeline` is selected and `codecommit` is in its Wirable Parameters as a source, compose's auto-include resolver (Step 3.1) MUST add codecommit. The builder is prompted ONCE for `RepositoryName` (during codecommit's Compose Config), and codepipeline's `SourceRepoName` parameter is wired to codecommit's output via `$(eval)` in prepare.mk.

#### 3.2 Derive Wiring Map

Build the complete wiring map from all stacks' `## Wirable Parameters` sections. Each row in a stack's wirable parameters table becomes a wiring entry:

```
source.stack  = Source Stack column value (tier name)
source.output = Source Output column value
target.stack  = the stack that owns this Wirable Parameters table (tier name)
target.parameter = Parameter column value
notes         = Notes column value
```

#### 3.3 Derive Deploy Order

Build the deployment dependency graph:

1. For each wiring entry, the target stack depends on the source stack.
2. If a stack has a `## Deploy Order` section with explicit ordering constraints (e.g., "Queue deploys before backend"), enforce these.
3. Topologically sort the graph to produce deployment order.
4. Within the same lifecycle, respect dependencies. Across lifecycles, all prepare stacks deploy before all deploy stacks.

#### 3.4 Apply Feature Flag Auto-Wiring

When the composition includes stacks that are wired together via feature flags, automatically enable the corresponding flags:

- **If `queue` and `backend` are both selected**: Set `EnableSqsIntegration=true` on backend (enables SQS wiring parameters). This is inferred from backend's Wirable Parameters having `SqsQueueUrl` and `SqsSendQueueArns` with source `queue`, gated by the `EnableSqsIntegration` feature flag.

Run validation procedures V3 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

---

### Step 4: Validate Wiring

Run validation procedure V4 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

---

## Phase 2: Confirm

### Step 5: Composition Summary and Confirmation

Display a summary of what will be generated. Check if generated artifacts already exist (re-composition scenario).

#### Summary Display

```
Composition Summary: {tier1} + {tier2} + ...
Project: {APP_NAMESPACE} | Environment: {APP_ENV} | Region: {AWS_REGION}

Stack Inventory:
  | Stack | Tier | Template | Lifecycle |
  |-------|------|----------|-----------|
  | ipa.stack.{tier1} | {tier1} | infra/cfn/{tier1}/{tier1}.yml | prepare |
  | ipa.stack.{tier2} | {tier2} | infra/cfn/{tier2}/{tier2}.yml | deploy |
  | ... | ... | ... | ... |

Deployment Order:
  1. {APP_NAMESPACE}-{APP_ENV}-{tier1} — depends on: none
  2. {APP_NAMESPACE}-{APP_ENV}-{tier2} — depends on: none
  3. {APP_NAMESPACE}-{APP_ENV}-{tier3} — depends on: {tier1}, {tier2}
  ...

Parameter Wiring:
  | Source | Output | → Target | Parameter |
  |--------|--------|----------|-----------|
  | {tier1} | {out1} | {tier3} | {param1} |
  | ... | ... | ... | ... |

Artifacts to generate:
  - scripts/prepare.mk                          (prepare Makefile — always generated)
  - scripts/deploy.mk
  - scripts/build.mk
  - scripts/post-deploy.mk                      (post-deploy Makefile — always generated)
  - scripts/env.mk                              (environment variable sync — always generated)
  - scripts/test.mk
  - scripts/SECURITY-DISPOSITION.md
```

If existing artifacts are detected, add: "**Re-composition**: Existing artifacts will be overwritten. Custom dispositions in SECURITY-DISPOSITION.md will be preserved."

Display: **"Generating artifacts..."** and proceed directly to artifact generation (Phase 3). Do NOT ask for confirmation — composition is a local, idempotent operation that can be safely re-run via `/ipa-compose` at any time.

Note at the bottom of the summary: "Re-run `/ipa-compose` at any time to regenerate. All artifacts are idempotent."

---

## Phase 3: Generate

### Step 6: Generate deploy.mk

**Before generating deploy.mk**, filter the stack list: include only stacks with `lifecycle = "deploy"`. Stacks with `lifecycle = "prepare"` are excluded from deploy.mk entirely — they appear in prepare.mk (generated in Step 6a). This filtering affects the aggregate `deploy:` target, per-stack `deploy-{suffix}` targets, the aggregate `teardown:` target, per-stack `teardown-{suffix}` targets, and the `.PHONY` declaration.

Create `scripts/` directory if it does not exist. Write `scripts/deploy.mk`.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) for exact syntax patterns. Generate:

1. **Header**: Comment block with composed stack tier names (e.g., `# Deploy targets for backend + frontend + queue`), usage instructions, `-include .env`, `.PHONY` declarations.
2. **Aggregate deploy target**: `deploy: deploy-{tier1} deploy-{tier2} ... deploy-{tierN}` in deployment order.
3. **Per-stack deploy targets**: For each stack in deployment order:
   - Add Make dependency prerequisites from the wiring-derived dependency graph.
   - For each wiring entry targeting this stack with `target.parameter`: add a `$(eval)` line to capture the source output via `aws cloudformation describe-stacks --query`.
   - Write the `aws cloudformation deploy` command with `--stack-name`, `--template-file`, `--parameter-overrides`, and `--no-fail-on-empty-changeset`.
   - Include Compose Config parameter overrides and auto-wired feature flags in `--parameter-overrides`.
   - Add `--capabilities CAPABILITY_NAMED_IAM` if the stack requires it.
4. **Aggregate teardown target**: `teardown: teardown-{tierN} ... teardown-{tier1}` in reverse deployment order.
5. **Per-stack teardown targets**: `aws cloudformation delete-stack --stack-name $(APP_NAMESPACE)-$(APP_ENV)-{tier}` followed by `aws cloudformation wait stack-delete-complete --stack-name $(APP_NAMESPACE)-$(APP_ENV)-{tier}`.

**Logs pre-check pattern**: When a deploy target references `$(LOG_BUCKET_NAME)` from `.env` (wired from `logs` prepare stack), emit a pre-check that validates the `{ns}-{env}-logs` CloudFormation stack exists. Exit with a clear error message if missing. See [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) Logs Pre-Check Pattern.

**Critical rules**:
- All stack names use `$(APP_NAMESPACE)-$(APP_ENV)-{tier}` — never literal values.
- All targets are `.PHONY`.
- Teardown is in exact reverse of deployment order.
- `$(eval ... $(shell ...))` lines MUST use conditional profile/region: `$(if $(AWS_PROFILE),--profile $(AWS_PROFILE),) $(if $(AWS_REGION),--region $(AWS_REGION),)`. Make's `$(shell)` does not inherit `export`-ed variables — these conditionals pass credentials when set (local dev) and omit them when empty (CI/CD IAM role).

---

### Step 6a: Generate prepare.mk

Always generate `scripts/prepare.mk`. Filter the stack list to include only stacks with `lifecycle = "prepare"`.

**If zero stacks have prepare lifecycle**: Write a no-op prepare.mk with the header block and a no-op target:
```makefile
prepare:
	@echo "No prepare targets for this composition"
```

**If one or more stacks have prepare lifecycle**: Write the full prepare.mk.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) prepare.mk template. Generate:

1. **Header**: Comment block with usage instructions, `-include .env`, `.PHONY` declarations.
2. **Aggregate prepare target**: `prepare: prepare-{tier1} prepare-{tier2} ...` in deployment order (filtered to prepare stacks).
3. **Per-stack prepare targets**: For each prepare stack in deployment order:
   - Add Make dependency prerequisites (only against other prepare stacks).
   - For wiring entries between prepare stacks: add `$(eval)` lines to capture outputs.
   - Write the `aws cloudformation deploy` command.
   - Add `--capabilities CAPABILITY_NAMED_IAM` if required.
4. **Aggregate teardown target**: `teardown-prepare: teardown-{tierN} ... teardown-{tier1}` in reverse order.
5. **Per-stack teardown targets**: `aws cloudformation delete-stack` + `wait stack-delete-complete`.

**Note**: Environment variable writes (OIDC, ECR, SQS) are no longer generated in prepare.mk. They are consolidated in `env.mk` (see Step 6c). The prepare chain is simplified to: `prepare-cognito → prepare-ecr` (direct dependency, no env targets). When `codepipeline` is in the composition, `prepare-codecommit` and `prepare-codepipeline` are appended to the chain.

**Security source stack special case**: When a wirable parameter's Source Stack is `security`, do NOT generate a `$(eval)` line to query the security CloudFormation stack. Instead, reference the `.env` variable directly (e.g., `CodeBuildRoleArn=$(APP_CODEBUILD_ROLE_ARN)`). The security stack is deployed by `/ipa-security` outside the compose/prepare flow, and its outputs are written to `.env` by that skill.

**Critical rules**:
- Same naming/variable conventions as deploy.mk
- All targets are `.PHONY`
- Teardown is in exact reverse of prepare deployment order
- Teardown comment: `# === TEARDOWN (manual only — never auto-deleted by /ipa-destroy) ===`
- `$(eval ... $(shell ...))` lines MUST use conditional profile/region.

---

### Step 6b: Generate post-deploy.mk

Always generate `scripts/post-deploy.mk`. Read the **Post-Deploy Steps** section below to determine which steps apply based on the stacks in the composition.

**If no post-deploy steps apply**: Write a no-op post-deploy.mk.

**If post-deploy steps exist**: Write the full post-deploy.mk.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) post-deploy.mk template. Generate:

1. **Header**: Comment block with usage instructions, `-include .env`, `.PHONY` declarations.
2. **Aggregate post-deploy target**: `post-deploy: {step1} {step2} ... {stepN}` in dependency order.
3. **Per-step targets**: For each post-deploy step:
   - Add Make dependency prerequisites from the step's "Depends on" declaration.
   - For each stack output reference: add a `$(eval)` line via `aws cloudformation describe-stacks --query`.
   - **Use tier names** for `--stack-name` (e.g., `backend` for ApiUrl/FunctionArn, `frontend` for AppUrl/BucketName/DistributionId).
   - Write the operational command.
4. No teardown targets — post-deploy steps are operational, not infrastructure.

#### OIDC Variables from .env

When generating post-deploy targets that reference Cognito outputs (IssuerUrl, UserPoolClientId, EndSessionEndpoint), do NOT generate `$(eval)` lines. Instead, reference the `.env` variables directly:
- `$(OIDC_ISSUER)` instead of fetching IssuerUrl
- `$(OIDC_CLIENT_ID)` instead of fetching UserPoolClientId
- `$(OIDC_END_SESSION_ENDPOINT)` instead of fetching EndSessionEndpoint

These variables are written to `.env` by `update-env-cognito` in env.mk (invoked from post-deploy.mk).

#### update-env Target

Always generate an `update-env` target as the **first step** in the `post-deploy:` chain. This target invokes `env.mk` conditionally:

```makefile
update-env:
	@if [ -f ./.env ]; then $(MAKE) -f scripts/env.mk update-env; fi
```

This ensures CI/CD (no `.env` file) skips the env sync. The `update-env` target must appear in the `.PHONY` declaration and as the first prerequisite of the aggregate `post-deploy:` target.

**Critical rules**:
- All stack names use `$(APP_NAMESPACE)-$(APP_ENV)-{tier}` — never literal values.
- All targets are `.PHONY`.
- Post-deploy targets use descriptive names (e.g., `configure-frontend`), not `post-deploy-{tier}`.
- The `update-cognito-callback` target must pass ALL parameters that `prepare-cognito` passes, plus the updated `CallbackURL`.
- `$(eval ... $(shell ...))` lines MUST use conditional profile/region.

---

### Step 6c: Generate env.mk

Always generate `scripts/env.mk`. This file consolidates all `.env` writes — syncing deployed stack outputs to `.env` for local dev.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) env.mk template. Generate:

1. **Header**: Comment block with usage instructions, `-include .env`, `.PHONY` declarations.
2. **Aggregate target**: `update-env: update-env-{tier1} update-env-{tier2} ...` listing all per-stack env targets.
3. **Per-stack env targets**: For each stack in the composition that has `.env`-relevant outputs:
   - **cognito** → `update-env-cognito` (writes OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_DISCOVERY_URL, OIDC_END_SESSION_ENDPOINT, OIDC_USER_POOL_ID)
   - **ecr** → `update-env-ecr` (writes ECR_REPO_URI)
   - **queue** → `update-env-sqs` (writes SQS_QUEUE_URL)
   - **codepipeline** → `update-env-pipeline` (writes PIPELINE_STACK_NAME, PIPELINE_NAME, CODEBUILD_PROJECT_NAME, CODECOMMIT_STACK_NAME, CODECOMMIT_REPO_NAME, CODECOMMIT_CLONE_URL)

Each target uses `$(eval)` to query CloudFormation outputs and `grep -v` + `echo` to idempotently write to `.env`.

**Stack presence rules**:
- Generate `update-env-logs` when the composition includes `logs` (any lifecycle)
- Generate `update-env-cognito` when the composition includes `cognito` (any lifecycle)
- Generate `update-env-ecr` when the composition includes `ecr` (any lifecycle)
- Generate `update-env-sqs` when the composition includes `queue` (any lifecycle)
- Generate `update-env-pipeline` when the composition includes `codepipeline` (any lifecycle)
- If no stacks with env outputs are present, generate a no-op: `update-env: @echo "No environment variables to sync"`

**Critical rules**:
- All `$(eval)` variables use `_VAL` suffix to prevent collision with `.env`-sourced variables
- `$(eval ... $(shell ...))` lines MUST use conditional profile/region
- All targets are `.PHONY`

---

### Step 7: Generate build.mk

Write `scripts/build.mk`. Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) for syntax.

Scan each stack skill's `## Build Requirements` section. Extract every column from the table (Type, Suffix, Dockerfile, Description):
- **Type: container** → generate `build-{suffix}` target using `$(call ecr-login)` and `$(call docker-build-push,...)` helpers from `scripts/util/docker.mk`. Use the **Dockerfile** column value as the `{dockerfile-path}` argument — do NOT infer or construct the path from the suffix.
- **Type: frontend** → generate `build-frontend` target with `cd frontend && npm ci && npm run build`
- **No Build Requirements section** → no target for this stack

If no stacks have build requirements, write a no-op `build` target.

---

### Step 8: Generate test.mk

Write `scripts/test.mk`. Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) for syntax.

Generate a stub `test` target with a no-op echo. Test content will be added later.

---

### Step 9: Generate Security Disposition Register

Write `scripts/SECURITY-DISPOSITION.md`.

#### First-Time Composition

Read the **Known Deferrals** section below. Filter to only include deferrals for stacks that are in the current composition.

```markdown
# Security Disposition Register: {tier1} + {tier2} + ...

> Generated by /ipa-compose on {YYYY-MM-DD}.
> This register tracks known security findings and their dispositions.

## Stack Deferrals

| ID | Stack | Finding | Disposition | Rationale |
|----|-------|---------|-------------|-----------|
| DEF-001 | {tier} | {description} | Accepted — POC scope | {rationale} |
| ... | ... | ... | ... | ... |

## Custom Dispositions

<!-- Add project-specific security findings and dispositions below this line. -->
<!-- This section is preserved across re-composition by /ipa-compose. -->
```

#### Re-Composition (Custom Dispositions Preservation)

If `scripts/SECURITY-DISPOSITION.md` already exists:

1. Read the existing file.
2. Find the `## Custom Dispositions` section.
3. Extract everything from `## Custom Dispositions` to the end of the file — this is the preserved content.
4. Regenerate the `## Stack Deferrals` section from the Known Deferrals for stacks in the composition.
5. Write the new file: header + regenerated Stack Deferrals + preserved Custom Dispositions content.

---

## Phase 4: Report

### Step 10: Completion Report

Display a structured report:

```
Composition Complete: {tier1} + {tier2} + ...

Generated artifacts:
  ✓ scripts/prepare.mk                         (prepare Makefile — run once)
  ✓ scripts/deploy.mk                          (deployment Makefile)
  ✓ scripts/build.mk                           (build Makefile)
  ✓ scripts/post-deploy.mk                     (post-deploy Makefile)
  ✓ scripts/env.mk                             (environment variable sync — .env writes)
  ✓ scripts/test.mk                            (test Makefile)
  ✓ scripts/SECURITY-DISPOSITION.md              (security disposition register)

Summary:
  Stacks composed: {N}
  Wiring entries resolved: {N}
  Build targets generated: {N}
  CFN templates validated: {N}

Next steps:
  • Review generated artifacts
  • Run `make -f scripts/test.mk test-validate` to validate templates
  • Run `/ipa-prepare` to deploy one-time prerequisites (ECR, etc.)
  • Run `/ipa-deploy` to deploy the composed stacks
```

Note: For fresh compose, the report shows total stacks only.

---

## Post-Deploy Steps

Post-deploy steps are selected based on which stacks are in the composition. They run after all CloudFormation deploys succeed. Post-deploy runs automatically within `/ipa-deploy` — no separate invocation needed.

### Always included

#### update-env
- Action: Sync stack outputs to .env (conditional: only if .env exists)
- Invokes: `scripts/env.mk` update-env target
- Notes: CI/CD skips this (no .env file). Local dev gets OIDC_*, ECR_REPO_URI, SQS_QUEUE_URL written to .env.

### When `backend` is in composition (with EnablePassengersTable=true)

#### load-data
- Action: Load sample Titanic passenger data from CSV into DynamoDB table
- Script: `cd app-lib && uv run python -m app_lib.features.passengers.util.load_dynamodb_util`
- Depends on: (none within post-deploy)
- Notes: Uses PutItem (upsert) — safe to re-run. Reads from app-lib/src/app_lib/assets/datasets/titanic/walkthrough_titanic.csv

### When `frontend` is in composition

#### configure-frontend
- Action: Generate web-client/dist/config.js with runtime configuration
- Script: scripts/util/configure_frontend.py
- Depends on: (none within post-deploy)
- Stack outputs:
  - backend → ApiUrl
  - frontend → AppUrl
- .env variables: OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_END_SESSION_ENDPOINT
- **When `queue` is also in composition**: Append `--enable-feature jobs` to the configure_frontend.py command

#### upload-frontend
- Action: Sync web-client/dist/ to S3 bucket
- Depends on: configure-frontend
- Stack outputs:
  - frontend → BucketName
- Command: aws s3 sync web-client/dist/ s3://{BucketName}/ --delete

#### invalidate-cf
- Action: Create CloudFront cache invalidation and wait for completion
- Depends on: upload-frontend
- Stack outputs:
  - frontend → DistributionId
- Command: aws cloudfront create-invalidation + aws cloudfront wait invalidation-completed

#### update-cognito-callback
- Action: Update Cognito callback/logout URLs — add CloudFront domain alongside localhost
- Depends on: invalidate-cf
- Stack outputs:
  - frontend → AppUrl
- Command: aws cloudformation deploy (Cognito stack with CallbackURL={AppUrl}/authentication/callback)
- Notes: Passes ALL original prepare-cognito parameters plus updated CallbackURL. The localhost callback remains — CloudFront URL is added as additional allowed callback.

#### update-backend-cors
- Action: Update API Gateway v2 CORS origin with CloudFront domain
- Depends on: update-cognito-callback
- Stack outputs:
  - frontend → AppUrl
- Notes: Re-deploys backend stack with AllowedOrigin set to CloudFront URL. Must pass ALL original deploy-backend parameters plus updated frontend AppUrl for CORS.
  **When `queue` is also in composition**: Must also include the SQS integration parameters (EnableSqsIntegration=true, SqsQueueUrl, SqsSendQueueArns) queried from the queue stack — same as the deploy-backend target.

---

## Known Deferrals

Security deferrals by stack, included in SECURITY-DISPOSITION.md only when the stack is in the composition.

### frontend

| ID | Finding | Rationale |
|----|---------|-----------|
| S3-1 | No bucket versioning | POC scope |
| CF-1 | No custom domain / ACM certificate | POC uses *.cloudfront.net |
| CF-2 | No WAF | POC scope + HTTP API v2 does not support WAF |
| CF-3 | PriceClass_100 only | POC — US/Canada/Europe only |
| CF-4 | Short DefaultTTL (300s) | POC — production should tune per content type |
| APIGW-1 | CORS origin `*` during initial deploy | CloudFront domain unknown at API deploy time; auto-wired in post-deploy |

### queue

| ID | Finding | Rationale |
|----|---------|-----------|
| SQS-1 | No FIFO queue support | POC scope — standard queue sufficient |
| SQS-2 | No SSE streaming for job status | POC scope |

### codecommit

| ID | Finding | Rationale |
|----|---------|-----------|
| CC-1 | No KMS encryption at rest | POC scope — CodeCommit uses SSE by default |

### codepipeline

| ID | Finding | Rationale |
|----|---------|-----------|
| CP-1 | No KMS encryption for artifacts | POC scope — SSE-S3 default encryption used |
| CP-2 | No cross-account pipeline support | POC scope — single-account deployment |
| CP-3 | No approval stage | POC scope — auto-deploys on push |
