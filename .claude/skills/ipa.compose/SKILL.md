---
name: ipa.compose
description: "Compose a deployment pattern from stack skills and generate executable artifacts
  (Makefiles, runbook, security disposition). Use when the user says 'compose', 'generate
  deployment', or invokes /ipa.compose."
model: opus
---

# /ipa.compose — Compose Deployment Pattern

This skill reads pattern definitions and stack skills, composes them into a project-specific deployment configuration, and generates five executable artifacts: three Makefiles (deploy, build, test), an infrastructure runbook, and a security disposition register.

**Prerequisite workflow**: `/ipa.init` → `/ipa.security` → **`/ipa.compose`** → `/ipa.deploy`

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
| `APP_BUILDER_ROLE_ARN` | `/ipa.security` |

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

To determine stack count for the menu, quickly scan each pattern's `## Stack Sequence` section and count `ipa.stack.*` references.

Store the selected pattern name and directory path.

---

### Step 3: Read Pattern Definition

Read the selected pattern's files from `patterns/{name}/`:

#### 3.1 PATTERN.md

Extract these sections:

- **Stack Sequence**: Numbered list of `ipa.stack.{service}` references with dependency declarations. Extract: stack names, deployment order, dependencies.
- **Teardown Sequence**: Reverse-order list for teardown targets.
- **Known Deferrals** (optional): List of security deferrals for the disposition register.

#### 3.2 Wiring (from PATTERN.md)

Read the `## Wiring` section from `PATTERN.md`. This contains a structured YAML wiring map. Each entry has:
- `source.stack` and `source.output`
- `target.stack` and `target.parameter` OR `target.env`
- `notes`

Store the full wiring map for validation and Makefile generation.

#### 3.3 ARCHITECTURE.md

Read the full content of `patterns/{name}/ARCHITECTURE.md`. This will be copied verbatim into the runbook.

Run validation procedures V2 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

---

### Step 4: Read Stack Skills

For each `ipa.stack.{service}` referenced in the Stack Sequence, read `.claude/skills/ipa.stack.{service}/SKILL.md` and extract:

| Section | Extract | Used For |
|---------|---------|----------|
| CloudFormation Contract | Template path, service suffix, capabilities | deploy.mk targets, stack naming |
| Parameters | Parameter name list | Wiring validation |
| Outputs | Output name list | Wiring validation, `cfn-outputs` calls |
| Build Requirements (optional) | Type, command | build.mk targets |

Run validation procedures V3 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

---

## Phase 2: Confirm

### Step 5: Composition Summary and Confirmation

Validate wiring cross-references before displaying the summary. Run validation procedure V4 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

Display a summary of what will be generated. Check if generated artifacts already exist (re-composition scenario).

#### Summary Display

```
Composition Summary: {pattern_name}
Project: {APP_NAMESPACE} | Environment: {APP_ENV} | Region: {AWS_REGION}

Stack Inventory:
  | Stack | Suffix | Template |
  |-------|--------|----------|
  | ipa.stack.{svc1} | {sfx1} | infra/cfn/{svc1}.yml |
  | ... | ... | ... |

Deployment Order:
  1. {APP_NAMESPACE}-{APP_ENV}-{sfx1} — depends on: none
  2. {APP_NAMESPACE}-{APP_ENV}-{sfx2} — depends on: none
  3. {APP_NAMESPACE}-{APP_ENV}-{sfx3} — depends on: {sfx1}, {sfx2}
  ...

Parameter Wiring:
  | Source | Output | → Target | Parameter/Env |
  |--------|--------|----------|---------------|
  | {sfx1} | {out1} | {sfx3} | {param1} |
  | ... | ... | ... | ... |

Artifacts to generate:
  - scripts/deploy.mk
  - scripts/build.mk
  - scripts/test.mk
  - docs/infra/runbook.md
  - docs/infra/security-disposition.md
```

If existing artifacts are detected, add: "**Re-composition**: Existing artifacts will be overwritten. Custom dispositions in security-disposition.md will be preserved."

Ask: "Generate these artifacts? (yes to proceed, no to cancel):"

- **If confirmed**: proceed to artifact generation.
- **If declined**: exit — "Composition cancelled. No files were written."

---

## Phase 3: Generate

### Step 6: Generate deploy.mk

Create `scripts/` directory if it does not exist. Write `scripts/deploy.mk`.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) for exact syntax patterns. Generate:

1. **Header**: Comment block with usage instructions, `-include .env`, `.PHONY` declarations.
2. **Aggregate deploy target**: `deploy: deploy-{sfx1} deploy-{sfx2} ... deploy-{sfxN}` in deployment order.
3. **Per-stack deploy targets**: For each stack in deployment order:
   - Add Make dependency prerequisites from the Stack Sequence dependencies.
   - For each wiring entry targeting this stack with `target.parameter`: add a `$(eval)` line to capture the source output via `uv run --project utils deploy cfn-outputs`.
   - Write the `uv run --project utils deploy cfn` command with `--stack-name`, `--template`, and `--parameter-overrides`.
   - Add `--capabilities CAPABILITY_NAMED_IAM` if the stack requires it.
4. **Aggregate teardown target**: `teardown: teardown-{sfxN} ... teardown-{sfx1}` in reverse deployment order.
5. **Per-stack teardown targets**: `uv run --project utils deploy cfn-delete --stack-name $(APP_NAMESPACE)-$(APP_ENV)-{suffix}`.

**Critical rules**:
- All stack names use `$(APP_NAMESPACE)-$(APP_ENV)-{suffix}` — never literal values.
- All targets are `.PHONY`.
- Teardown is in exact reverse of deployment order.

---

### Step 7: Generate build.mk

Write `scripts/build.mk`. Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) for syntax.

Scan each stack skill's `## Build Requirements` section:
- **Type: container** → generate `build-{function}` target with `uv run --project utils build docker --tag $(APP_NAMESPACE)-$(APP_ENV)-{function}`
- **Type: frontend** → generate `build-frontend` target with `cd frontend && npm ci && npm run build`
- **No Build Requirements section** → no target for this stack

If no stacks have build requirements, write a no-op `build` target.

---

### Step 8: Generate test.mk

Write `scripts/test.mk`. Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) for syntax.

Always include:
- `test-unit`: `uv run --project utils test unit`
- `test-security`: `uv run --project utils test security`
- `test-cfn-lint`: one `uv run --project utils test cfn-lint --template {path}` per CloudFormation template referenced by stacks in the pattern.

Aggregate target: `test: test-unit test-security test-cfn-lint`.

---

### Step 9: Generate Runbook

Create `docs/infra/` directory if it does not exist. Write `docs/infra/runbook.md`.

Load [RUNBOOK_TEMPLATE.md](RUNBOOK_TEMPLATE.md) for section structure. Generate all sections:

1. **Title and Overview**: Pattern name, generation date, architecture from ARCHITECTURE.md, stack summary table.
2. **Prerequisites**: AWS CLI, uv, Make. Add Docker if any stack has container builds, Node.js if frontend builds.
3. **Configuration**: `.env.example` copy instructions, variable table.
4. **Environment Variables**: Base rows for `APP_REGION`, `APP_ENV`, `APP_NAMESPACE` from `.env`, plus one row per wiring entry with `target.env`.
5. **Security Setup**: Security stack verification command.
6. **Build**: `make -f scripts/build.mk build` with per-target descriptions if applicable.
7. **Deployment**: Per-stack deployment steps in order, with `make -f scripts/deploy.mk deploy-{suffix}` commands, descriptions, dependencies, and outputs. Include aggregate `deploy` command.
8. **Verification**: Per-stack status check commands.
9. **Teardown**: Reverse-order deletion with aggregate `teardown` command and individual steps.
10. **Troubleshooting**: ROLLBACK_COMPLETE, Permission Denied, Resource Already Exists.

**Critical rule**: The runbook MUST NOT reference IPA skills, Claude Code, or the AI agent. It is a self-contained customer deliverable.

---

### Step 10: Generate Security Disposition Register

Write `docs/infra/security-disposition.md`.

#### First-Time Composition

```markdown
# Security Disposition Register: {Pattern Name}

> Generated by /ipa.compose on {YYYY-MM-DD}.
> This register tracks known security findings and their dispositions.

## Pattern Deferrals

{Copy each Known Deferral from the pattern definition, formatted as a table:}

| ID | Finding | Disposition | Rationale |
|----|---------|-------------|-----------|
| DEF-001 | {description} | Accepted — POC scope | {rationale from pattern} |
| ... | ... | ... | ... |

## Custom Dispositions

<!-- Add project-specific security findings and dispositions below this line. -->
<!-- This section is preserved across re-composition by /ipa.compose. -->
```

#### Re-Composition (Custom Dispositions Preservation)

If `docs/infra/security-disposition.md` already exists:

1. Read the existing file.
2. Find the `## Custom Dispositions` section.
3. Extract everything from `## Custom Dispositions` to the end of the file — this is the preserved content.
4. Regenerate the `## Pattern Deferrals` section from the current pattern's Known Deferrals.
5. Write the new file: header + regenerated Pattern Deferrals + preserved Custom Dispositions content.

---

## Phase 4: Report

### Step 11: Completion Report

Display a structured report:

```
Composition Complete: {pattern_name}

Generated artifacts:
  ✓ scripts/deploy.mk                         (deployment Makefile)
  ✓ scripts/build.mk                          (build Makefile)
  ✓ scripts/test.mk                           (test Makefile)
  ✓ docs/infra/runbook.md                     (customer deployment guide)
  ✓ docs/infra/security-disposition.md         (security disposition register)

Summary:
  Stacks composed: {N}
  Wiring entries resolved: {N}
  Build targets generated: {N}
  CFN templates validated: {N}

Next steps:
  • Review generated artifacts
  • Run `make -f scripts/test.mk test-cfn-lint` to validate templates
  • Run `/ipa.deploy` to deploy the composed pattern
```
