---
name: ipa.compose
description: "Compose a deployment pattern from stack skills and generate executable artifacts
  (Makefiles, security disposition). Use when the user says 'compose',
  'generate deployment', or invokes /ipa.compose."
model: opus
---

# /ipa.compose — Compose Deployment Pattern

This skill reads pattern definitions and stack skills, composes them into a project-specific deployment configuration, and generates six executable artifacts: five Makefiles (prepare, deploy, build, post-deploy, test) and a security disposition register.

**Prerequisite workflow**: `/ipa.init` → `/ipa.security` → **`/ipa.compose`** → `/ipa.prepare` → `/ipa.deploy`

---

## Phase 0: Parse Intent

This phase runs before Phase 1. It parses the builder's input, classifies arguments, detects whether an existing composition exists, and determines the composition mode.

### Step 0.1: Classify Input Arguments

Read the arguments supplied with the `/ipa.compose` invocation. For each token:

1. Check if it matches a directory name in `patterns/` (relative to this SKILL.md) → classify as **pattern**
2. If the token matches no pattern → classify as **natural language context**

For natural language tokens, attempt to resolve to known patterns. Lean on the AI agent's language understanding:

1. **Scan patterns**: For each pattern directory in `patterns/`, read the first line of `PATTERN.md` for the description. Check if the natural language token semantically relates to the pattern name or description (e.g., "knowledge base" matches `bedrock-knowledge-base`, "API backend" matches `react-rest-lambda`).

2. **Resolve matches**:
   - **Exactly one match**: Auto-classify. Display: "Interpreted `{natural language}` as `{matched-name}`. Correct? (yes/no):"
   - **Multiple matches**: Present all matches and ask the builder to select.
   - **No match**: Ask the builder to clarify: "Could not resolve `{natural language}` to a known pattern. Available patterns: {list}."

Store the classified tokens: list of identified patterns and any unresolved natural language.

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

| deploy.mk exists? | Args contain pattern(s)? | Mode |
|---|---|---|
| No | Yes | **Fresh compose** — proceed to Phase 1 with identified pattern(s) |
| No | No | **Pattern discovery** — proceed to Phase 1 Step 2 |
| Yes | Yes | **Fresh compose (overwrite)** — proceed to Phase 1 with identified pattern(s) |
| Yes | No | **Idempotent refresh** — proceed to Step 0.3a, then Phase 1 |

---

### Step 0.3a: Extract Pattern Name from deploy.mk (Idempotent Refresh Only)

Read `scripts/deploy.mk` header to determine which pattern(s) were previously composed:

1. Match `# Deploy targets for {name}` in the first 5 lines.
   - Extract the pattern name(s). If the header contains `+`, multiple patterns were composed (e.g., `react-rest-lambda + sqs-lambda pattern`).
   - If `manual_edit_detected` is true:
     - Warn: "deploy.mk appears to have been manually edited. Re-composing will overwrite all manual changes. Proceed? (yes to overwrite, no to cancel):"
     - If declined: exit with "Composition cancelled. No files were written."

2. Use the extracted pattern name(s) as input for Phase 1 (same as fresh compose).

---

## Phase 1: Validate

### Step 1: Pre-Flight Checks

#### 1.1 Verify .env Prerequisites

Read `.env` at the project root. Verify these variables exist and are non-empty:

| Variable | Written By |
|----------|------------|
| `APP_NAMESPACE` | `/ipa.init` |
| `APP_ENV` | `/ipa.init` |
| `AWS_REGION` | `/ipa.init` |
| `AWS_ACCOUNT_ID` | `/ipa.init` |
| `AWS_PROFILE` | `/ipa.init` |

Run validation procedure V1 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

Store all variable values for use in subsequent steps.

---

### Step 2: Pattern Discovery

Scan the `patterns/` subdirectory (relative to this SKILL.md) for subdirectories. Each subdirectory name is a pattern name. For each match, read the first line of `PATTERN.md` (expected format: `# Pattern: {name}`) for the description.

**If zero patterns found**: STOP — "No patterns found in `patterns/` directory. Author a pattern definition (e.g., `patterns/react-rest-lambda/PATTERN.md`) before running `/ipa.compose`."

**If exactly one pattern found**: Auto-select it. Display: "Found one pattern: **{name}** — {description}. Proceeding with this pattern."

**If multiple patterns found**: Display a numbered selection menu:

```
Available patterns:

  1. {name1} ({N1} stacks) — {description1}
  2. {name2} ({N2} stacks) — {description2}
  ...

Select a pattern (enter number):
```

To determine stack count, scan each pattern's `## Stack Sequence` section and count `ipa.stack.*` references.

Store the selected pattern name(s) and directory path(s).

---

### Step 3: Read Pattern Definition(s)

For each selected pattern, read files from `patterns/{name}/`:

#### 3.1 PATTERN.md

Extract these sections:

- **Stack Sequence**: List of `ipa.stack.{service}` references with dependency declarations. Extract: stack names, deployment order, dependencies, and **lifecycle classification**.
  - **Parse `(prepare)` annotation**: The `(prepare)` token is optional and appears between the stack skill name and the em-dash description separator. If `(prepare)` is present, set `lifecycle = "prepare"`; otherwise set `lifecycle = "deploy"`. This classification determines which Makefile receives the stack's targets (prepare.mk vs deploy.mk).
  - **Parse Config**: Extract parameter overrides from the `Config:` line (e.g., `FunctionName=fn EnablePassengersTable=true`). These become `--parameter-overrides` entries in the deploy target.
- **Deploy Ordering**: If the pattern declares explicit deploy ordering constraints (e.g., "Queue deploys before backend"), record these for enforcement during multi-pattern merge.
- **Shared Stacks** (compose-only patterns): List of stacks from other patterns that are modified by this pattern. Extract the additional parameter overrides (e.g., `EnableSqsIntegration=true` applied to backend by sqs-lambda).
- **Shared Post-Deploy** (compose-only patterns): List of post-deploy steps from other patterns that are modified by this pattern. Extract additional CLI arguments (e.g., `--enable-feature jobs` appended to `configure-frontend` by sqs-lambda). Each entry names the target step and the arguments to append.
- **Teardown Sequence**: Reverse-order list for teardown targets. Prepare-classified stacks are excluded from teardown.
- **Known Deferrals** (optional): Security deferrals for the disposition register.
- **Post-Deploy** (optional): Ordered list of operational steps that run after all stacks deploy. Extract: step names, dependencies (within post-deploy), stack output references, commands. If absent, post-deploy.mk will be a no-op.

#### 3.2 Wiring (from PATTERN.md)

Read the `## Wiring` section from `PATTERN.md`. This contains a structured YAML wiring map. Each entry has:
- `source.stack` and `source.output`
- `target.stack` and `target.parameter`
- `notes`

Store the full wiring map for validation and Makefile generation.

#### 3.3 ARCHITECTURE.md

Read the full content of `patterns/{name}/ARCHITECTURE.md`. Store for reference during artifact generation.

#### 3.4 Multi-Pattern Merge

When composing multiple patterns (e.g., `react-rest-lambda + sqs-lambda`):

1. **Merge stack sequences**: Combine stacks from all patterns. Deduplicate shared stacks (same suffix) — keep one instance with the earliest lifecycle classification (prepare > deploy).
2. **Apply deploy ordering**: Respect pattern-declared ordering constraints. If pattern declares "queue deploys before backend", enforce this in the merged order.
3. **Combine wiring**: Union of all wiring entries from all patterns. Consolidated stacks have distinct parameter names, so no wiring conflicts occur.
4. **Merge parameter overrides**: When multiple patterns configure the same stack (e.g., backend gets `EnablePassengersTable=true` from react-rest-lambda and `EnableSqsIntegration=true` from sqs-lambda), combine all parameter overrides into a single `--parameter-overrides` line.
5. **Apply shared stack modifications**: Compose-only patterns declare modifications to shared stacks (e.g., sqs-lambda adds `EnableSqsIntegration=true` to backend). Apply these as additional parameter overrides on the shared stack's deploy target.
6. **Apply shared post-deploy modifications**: Compose-only patterns may declare modifications to existing post-deploy steps via `## Shared Post-Deploy`. For each declared modification, record the target step name and the additional CLI arguments to append. These are applied during post-deploy.mk generation (Step 6b) — the arguments are appended to the target step's command line.

Run validation procedures V2 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

---

### Step 4: Read Stack Skills

For each `ipa.stack.{service}` in the merged stack list, read `.claude/skills/ipa.stack.{service}/SKILL.md` and extract:

| Section | Extract | Used For |
|---------|---------|----------|
| Stack Identity | Template path, service suffix, capabilities | deploy.mk targets, stack naming |
| Parameters | Parameter name list, defaults | Wiring validation, `--parameter-overrides` |
| Feature Flags | Flag names, defaults, conditions | Parameter override validation |
| Outputs | Output name list | Wiring validation, `$(eval)` calls |
| Build Requirements (optional) | Type, Suffix, Dockerfile path | build.mk targets |

**Consolidated stack skills**: The primary solution stack skills are `ipa.stack.frontend`, `ipa.stack.backend`, and `ipa.stack.queue`. Each corresponds to a single tier template in `infra/cfn/{tier}/{tier}.yml`. Prepare stack skills (`ipa.stack.cognito`, `ipa.stack.ecr`) remain unchanged.

Run validation procedures V3 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

---

## Phase 2: Confirm

### Step 5: Composition Summary and Confirmation

Validate wiring cross-references before displaying the summary. Run validation procedure V4 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

Display a summary of what will be generated. Check if generated artifacts already exist (re-composition scenario).

#### Summary Display

```
Composition Summary: {pattern_name(s)}
Project: {APP_NAMESPACE} | Environment: {APP_ENV} | Region: {AWS_REGION}

Stack Inventory:
  | Stack | Suffix | Template | Lifecycle |
  |-------|--------|----------|-----------|
  | ipa.stack.{svc1} | {sfx1} | infra/cfn/{svc1}/{svc1}.yml | prepare |
  | ipa.stack.{svc2} | {sfx2} | infra/cfn/{svc2}/{svc2}.yml | deploy |
  | ... | ... | ... | ... |

Deployment Order:
  1. {APP_NAMESPACE}-{APP_ENV}-{sfx1} — depends on: none
  2. {APP_NAMESPACE}-{APP_ENV}-{sfx2} — depends on: none
  3. {APP_NAMESPACE}-{APP_ENV}-{sfx3} — depends on: {sfx1}, {sfx2}
  ...

Parameter Wiring:
  | Source | Output | → Target | Parameter |
  |--------|--------|----------|-----------|
  | {sfx1} | {out1} | {sfx3} | {param1} |
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

Display: **"Generating artifacts..."** and proceed directly to artifact generation (Phase 3). Do NOT ask for confirmation — composition is a local, idempotent operation that can be safely re-run via `/ipa.compose` at any time.

Note at the bottom of the summary: "Re-run `/ipa.compose` at any time to regenerate. All artifacts are idempotent."

---

## Phase 3: Generate

### Step 6: Generate deploy.mk

**Before generating deploy.mk**, filter the stack list: include only stacks with `lifecycle = "deploy"`. Stacks with `lifecycle = "prepare"` are excluded from deploy.mk entirely — they appear in prepare.mk (generated in Step 6a). This filtering affects the aggregate `deploy:` target, per-stack `deploy-{suffix}` targets, the aggregate `teardown:` target, per-stack `teardown-{suffix}` targets, and the `.PHONY` declaration.

Create `scripts/` directory if it does not exist. Write `scripts/deploy.mk`.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) for exact syntax patterns. Generate:

1. **Header**: Comment block with pattern name(s), usage instructions, `-include .env`, `.PHONY` declarations.
2. **Aggregate deploy target**: `deploy: deploy-{sfx1} deploy-{sfx2} ... deploy-{sfxN}` in deployment order.
3. **Per-stack deploy targets**: For each stack in deployment order:
   - Add Make dependency prerequisites from the Stack Sequence dependencies.
   - For each wiring entry targeting this stack with `target.parameter`: add a `$(eval)` line to capture the source output via `aws cloudformation describe-stacks --query`.
   - Write the `aws cloudformation deploy` command with `--stack-name`, `--template-file`, `--parameter-overrides`, and `--no-fail-on-empty-changeset`.
   - Include pattern-declared config parameters (e.g., `EnablePassengersTable=true`) and shared stack modifications (e.g., `EnableSqsIntegration=true`) in `--parameter-overrides`.
   - Add `--capabilities CAPABILITY_NAMED_IAM` if the stack requires it.
4. **Aggregate teardown target**: `teardown: teardown-{sfxN} ... teardown-{sfx1}` in reverse deployment order.
5. **Per-stack teardown targets**: `aws cloudformation delete-stack --stack-name $(APP_NAMESPACE)-$(APP_ENV)-{suffix}` followed by `aws cloudformation wait stack-delete-complete --stack-name $(APP_NAMESPACE)-$(APP_ENV)-{suffix}`.

**Critical rules**:
- All stack names use `$(APP_NAMESPACE)-$(APP_ENV)-{suffix}` — never literal values.
- All targets are `.PHONY`.
- Teardown is in exact reverse of deployment order.
- `$(eval ... $(shell ...))` lines MUST use conditional profile/region: `$(if $(AWS_PROFILE),--profile $(AWS_PROFILE),) $(if $(AWS_REGION),--region $(AWS_REGION),)`. Make's `$(shell)` does not inherit `export`-ed variables — these conditionals pass credentials when set (local dev) and omit them when empty (CI/CD IAM role).

---

### Step 6a: Generate prepare.mk

Always generate `scripts/prepare.mk`. Filter the stack list to include only stacks with `lifecycle = "prepare"`.

**If zero stacks have prepare lifecycle**: Write a no-op prepare.mk with the header block and a no-op target:
```makefile
prepare:
	@echo "No prepare targets for this pattern"
```

**If one or more stacks have prepare lifecycle**: Write the full prepare.mk.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) prepare.mk template. Generate:

1. **Header**: Comment block with usage instructions, `-include .env`, `.PHONY` declarations.
2. **Aggregate prepare target**: `prepare: prepare-{sfx1} prepare-{sfx2} ...` in deployment order (filtered to prepare stacks).
3. **Per-stack prepare targets**: For each prepare stack in deployment order:
   - Add Make dependency prerequisites (only against other prepare stacks).
   - For wiring entries between prepare stacks: add `$(eval)` lines to capture outputs.
   - Write the `aws cloudformation deploy` command.
   - Add `--capabilities CAPABILITY_NAMED_IAM` if required.
4. **Aggregate teardown target**: `teardown-prepare: teardown-{sfxN} ... teardown-{sfx1}` in reverse order.
5. **Per-stack teardown targets**: `aws cloudformation delete-stack` + `wait stack-delete-complete`.

**Note**: Environment variable writes (OIDC, ECR, SQS) are no longer generated in prepare.mk. They are consolidated in `env.mk` (see Step 6c). The prepare chain is simplified to: `prepare-cognito → prepare-ecr` (direct dependency, no env targets).

**Critical rules**:
- Same naming/variable conventions as deploy.mk
- All targets are `.PHONY`
- Teardown is in exact reverse of prepare deployment order
- Teardown comment: `# === TEARDOWN (manual only — never auto-deleted by /ipa.destroy) ===`
- `$(eval ... $(shell ...))` lines MUST use conditional profile/region.

---

### Step 6b: Generate post-deploy.mk

Always generate `scripts/post-deploy.mk`. Read the pattern's `## Post-Deploy` section.

**If no `## Post-Deploy` section exists**: Write a no-op post-deploy.mk.

**If post-deploy steps exist**: Write the full post-deploy.mk.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) post-deploy.mk template. Generate:

1. **Header**: Comment block with usage instructions, `-include .env`, `.PHONY` declarations.
2. **Aggregate post-deploy target**: `post-deploy: {step1} {step2} ... {stepN}` in dependency order.
3. **Per-step targets**: For each post-deploy step:
   - Add Make dependency prerequisites from the step's "Depends on" declaration.
   - For each stack output reference: add a `$(eval)` line via `aws cloudformation describe-stacks --query`.
   - **Use consolidated stack suffixes** for `--stack-name` (e.g., `backend` for ApiUrl/FunctionArn, `frontend` for AppUrl/BucketName/DistributionId).
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
- All stack names use `$(APP_NAMESPACE)-$(APP_ENV)-{suffix}` — never literal values.
- All targets are `.PHONY`.
- Post-deploy targets use descriptive names (e.g., `configure-frontend`), not `post-deploy-{suffix}`.
- The `update-cognito-callback` target must pass ALL parameters that `prepare-cognito` passes, plus the updated `CallbackURL`.
- `$(eval ... $(shell ...))` lines MUST use conditional profile/region.

---

### Step 6c: Generate env.mk

Always generate `scripts/env.mk`. This file consolidates all `.env` writes — syncing deployed stack outputs to `.env` for local dev.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) env.mk template. Generate:

1. **Header**: Comment block with usage instructions, `-include .env`, `.PHONY` declarations.
2. **Aggregate target**: `update-env: update-env-{sfx1} update-env-{sfx2} ...` listing all per-stack env targets.
3. **Per-stack env targets**: For each stack in the composition that has `.env`-relevant outputs:
   - **cognito** → `update-env-cognito` (writes OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_DISCOVERY_URL, OIDC_END_SESSION_ENDPOINT, OIDC_USER_POOL_ID)
   - **ecr** → `update-env-ecr` (writes ECR_REPO_URI)
   - **queue** → `update-env-sqs` (writes SQS_QUEUE_URL)

Each target uses `$(eval)` to query CloudFormation outputs and `grep -v` + `echo` to idempotently write to `.env`.

**Stack presence rules**:
- Generate `update-env-cognito` when the composition includes `cognito` (any lifecycle)
- Generate `update-env-ecr` when the composition includes `ecr` (any lifecycle)
- Generate `update-env-sqs` when the composition includes `queue` (any lifecycle)
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

```markdown
# Security Disposition Register: {Pattern Name}

> Generated by /ipa.compose on {YYYY-MM-DD}.
> This register tracks known security findings and their dispositions.

## Pattern Deferrals

{Copy each Known Deferral from all composed pattern definitions, formatted as a table:}

| ID | Finding | Disposition | Rationale |
|----|---------|-------------|-----------|
| DEF-001 | {description} | Accepted — POC scope | {rationale from pattern} |
| ... | ... | ... | ... |

## Custom Dispositions

<!-- Add project-specific security findings and dispositions below this line. -->
<!-- This section is preserved across re-composition by /ipa.compose. -->
```

#### Re-Composition (Custom Dispositions Preservation)

If `scripts/SECURITY-DISPOSITION.md` already exists:

1. Read the existing file.
2. Find the `## Custom Dispositions` section.
3. Extract everything from `## Custom Dispositions` to the end of the file — this is the preserved content.
4. Regenerate the `## Pattern Deferrals` section from all composed patterns' Known Deferrals.
5. Write the new file: header + regenerated Pattern Deferrals + preserved Custom Dispositions content.

---

## Phase 4: Report

### Step 10: Completion Report

Display a structured report:

```
Composition Complete: {pattern_name(s)}

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
  • Run `/ipa.prepare` to deploy one-time prerequisites (ECR, etc.)
  • Run `/ipa.security` to update IAM roles for new stacks
  • Run `/ipa.deploy` to deploy the composed pattern
```

Note: For fresh compose, the report shows total stacks only.
