---
name: ipa.compose
description: "Compose a deployment pattern from stack skills and generate executable artifacts
  (Makefiles, runbook, security disposition). Supports incremental composition — adding
  stacks or patterns to an existing composition. Use when the user says 'compose',
  'generate deployment', 'add stack', or invokes /ipa.compose."
model: opus
---

# /ipa.compose — Compose Deployment Pattern

This skill reads pattern definitions and stack skills, composes them into a project-specific deployment configuration, and generates six executable artifacts: four Makefiles (prepare, deploy, build, test), an infrastructure runbook, and a security disposition register.

Supports three composition modes:
- **Fresh compose**: Select a pattern, generate all artifacts (existing behavior)
- **Add stacks**: Add one or more stacks to an existing composition with auto-inferred wiring
- **Add pattern**: Layer an additional pattern onto an existing composition (expands to add-stacks)

**Prerequisite workflow**: `/ipa.init` → `/ipa.security` → **`/ipa.compose`** → `/ipa.prepare` → `/ipa.deploy`

---

## Phase 0: Parse Intent

This phase runs before Phase 1. It parses the builder's input, classifies arguments, detects whether an existing composition exists, determines the composition mode, and confirms understanding before proceeding.

### Step 0.1: Classify Input Arguments

Read the arguments supplied with the `/ipa.compose` invocation. For each token:

1. Check if it matches a directory name in `patterns/` (relative to this SKILL.md) → classify as **pattern**
2. Check if `.claude/skills/ipa.stack.{token}/SKILL.md` exists → classify as **stack**
3. If the token matches neither → classify as **natural language context**

For natural language tokens, attempt to resolve to known patterns or stacks. Lean on the AI agent's language understanding — you are an LLM and can interpret intent, synonyms, and context:

1. **Scan patterns**: For each pattern directory in `patterns/`, read the first line of `PATTERN.md` for the description. Check if the natural language token semantically relates to the pattern name or description (e.g., "knowledge base" matches a pattern named `bedrock-knowledge-base`, "API backend" matches `react-rest-lambda`).

2. **Scan stack skills**: For each `.claude/skills/ipa.stack.*/` directory, check if the natural language token semantically relates to the stack name (e.g., "container registry" matches `ipa.stack.ecr`, "authentication" matches `ipa.stack.cognito`).

3. **Resolve matches**:
   - **Exactly one match**: Auto-classify as the matched pattern or stack. Display: "Interpreted `{natural language}` as `{matched-name}`. Correct? (yes/no):"
   - **Multiple matches**: Present all matches and ask the builder to select:
     ```
     Multiple matches for "{natural language}":
       1. {match-1} (pattern) — {description}
       2. {match-2} (stack) — {description}
     Select (enter number):
     ```
   - **No match**: Ask the builder to clarify: "Could not resolve `{natural language}` to a known pattern or stack. Available patterns: {list}. Available stacks: {list}. Please specify the exact name."

Store the classified tokens: list of identified patterns, list of identified stacks, and any unresolved natural language.

---

### Step 0.2: Detect Existing Composition

Check if `scripts/deploy.mk` exists:

- **If exists**: An existing composition is present. Read the first 5 lines and look for the header comment `# Deploy targets for {name}`.
  - If the header contains `# Base: {name} | Added: {list}`, this is a previously extended composition. Extract the base pattern name and additions list.
  - If the header is missing or does not match the expected format, set a flag: `manual_edit_detected = true`.
  - Proceed to Step 0.3 with `existing_composition = true`.
- **If does not exist**: No existing composition. Set `existing_composition = false`.

---

### Step 0.3: Determine Composition Mode

Using the classified arguments (Step 0.1) and existing composition state (Step 0.2), determine the mode:

| deploy.mk exists? | Args contain pattern? | Args contain stacks? | Mode |
|---|---|---|---|
| No | Yes | Any | **Fresh pattern compose** — proceed to Phase 1 (existing flow) with the identified pattern |
| No | No | Yes | **ERROR**: "No existing composition found. Composition must begin with a pattern. Run `/ipa.compose {pattern-name}` first." |
| No | No | No | **Pattern discovery** — proceed to Phase 1 Step 2 (existing flow) |
| Yes | No | Yes | **Add stacks** — proceed to Step 0.3a, then Step 0.6 |
| Yes | Yes | Any | **Add pattern** — proceed to Step 0.3a, then Step 0.6 (expand pattern to stacks first) |
| Yes | No | No | **Idempotent refresh** — proceed to Step 0.3a, then re-read base pattern and regenerate all artifacts |

**Routing**:
- For **fresh pattern compose** and **pattern discovery** modes: skip the rest of Phase 0 and proceed directly to Phase 1 (the existing validation flow). All existing behavior is unchanged.
- For **add stacks**, **add pattern**, and **idempotent refresh** modes: continue to Step 0.3a.

---

### Step 0.3a: Parse deploy.mk (Composition State Recovery)

Read `scripts/deploy.mk` line by line and extract the current composition state:

#### Header Parsing

1. **Base pattern name**: Match `# Deploy targets for {name}` in the first 5 lines.
   - If the header contains ` + `, the composition has been extended. Example: `# Deploy targets for react-rest-lambda + sagemaker pattern`
   - If the header contains `# Base: {name} | Added: {list}`, extract both the base pattern and additions list.
   - If no recognizable header is found and `manual_edit_detected` is true:
     - Warn: "deploy.mk appears to have been manually edited (expected header comment not found). Re-composing will overwrite all manual changes. Proceed? (yes to overwrite, no to cancel):"
     - If declined: exit with "Composition cancelled. No files were written."

#### Stack List Extraction

2. **Stack list from aggregate deploy target**: Find the line matching `deploy:` followed by space-separated prerequisites. Each prerequisite `deploy-{suffix}` represents a composed stack.
   - Example: `deploy: deploy-ecr deploy-cognito deploy-lambda` → stacks: `["ecr", "cognito", "lambda"]`
   - The order of prerequisites IS the deployment order.

#### Per-Stack Details

3. **For each `deploy-{suffix}:` target**, extract:

   - **Dependencies**: Make prerequisites listed after the colon.
     - Example: `deploy-lambda: deploy-ecr deploy-cognito` → dependencies: `["ecr", "cognito"]`

   - **Template path**: Extract the `--template {path}` argument from the `uv run` command.
     - Example: `--template infra/cfn/ecr/ecr.yml` → template: `infra/cfn/ecr/ecr.yml`

   - **Wiring ($(eval) lines)**: Extract each `$(eval {VAR} := $(shell uv run --project utils deploy cfn-outputs --stack-name ... --output-key {OutputKey}))` line.
     - For each: extract the source stack suffix (from `--stack-name $(APP_NAMESPACE)-$(APP_ENV)-{suffix}`), the output key (from `--output-key {key}`), and the Make variable name.
     - The target parameter is identified from the `--parameter-overrides` line where the Make variable (`$(VAR)`) is used.

   - **Parameters**: Extract key-value pairs from `--parameter-overrides`.

#### Teardown Order

4. **Teardown order from aggregate teardown target**: Find `teardown:` and parse the prerequisite list in order.
   - Example: `teardown: teardown-lambda teardown-cognito teardown-ecr` → teardown order: `["lambda", "cognito", "ecr"]`

#### Validation of Parsed State

5. For each stack suffix found, verify the corresponding stack skill exists: `.claude/skills/ipa.stack.{service}/SKILL.md`.
   - If a referenced stack skill no longer exists on disk: ERROR — "Stack skill `ipa.stack.{service}` referenced in deploy.mk no longer exists at `.claude/skills/ipa.stack.{service}/SKILL.md`. Resolve this before re-composing."

6. If `scripts/deploy.mk` is empty or contains no recognizable deploy targets: treat as no existing composition, set `existing_composition = false`, and return to Step 0.3.

Store the parsed composition state (base pattern, stacks, deploy order, wiring, teardown order) for use in subsequent steps.

#### Prepare Stack Recovery

If `scripts/prepare.mk` exists and is non-empty:

1. Find `prepare:` aggregate target line and extract `prepare-{suffix}` prerequisites — these are the prepare-classified stacks.
2. For each `prepare-{suffix}:` target, extract the template path from `--template {path}`.
3. Store the prepare stack suffixes in the parsed composition state as `prepare_stacks`.

If `scripts/prepare.mk` does not exist or is empty, set `prepare_stacks = []`.

**Usage**: During merge (Step 0.6), stacks already in `prepare_stacks` retain their prepare classification. New stacks get classification from their pattern's Stack Sequence annotation.

---

### Step 0.4: Confirm Understanding

Display a summary for the builder to confirm:

**For add-stacks mode:**

```
Understood: Add {N} stack(s) ({stack-names}) to the existing
{base-pattern} composition.

Current stacks: {list of existing stack suffixes}
Adding: {list of new stack suffixes}

Proceed? (yes to continue, no to clarify):
```

**For add-pattern mode:**

```
Understood: Add pattern {pattern-name} ({N} stacks) to the existing
{base-pattern} composition.

Current stacks: {list of existing stack suffixes}
Adding from {pattern-name}: {list of new stack suffixes from the pattern}

Proceed? (yes to continue, no to clarify):
```

**For idempotent refresh:**

```
Understood: Refresh the existing {base-pattern} composition ({N} stacks).

Current stacks: {list of existing stack suffixes}
No new stacks will be added. Artifacts will be regenerated from current state.

Proceed? (yes to continue, no to clarify):
```

- If confirmed: proceed to Step 0.6 (or directly to Phase 3 for idempotent refresh).
- If declined: re-prompt "Please clarify what you'd like to compose, or type 'cancel' to exit."
- If cancelled: exit with "Composition cancelled. No files were written."

---

### Step 0.5: Handle Rejection and Removal Requests

If at any point the builder's input contains removal intent (e.g., "remove", "delete stack", "drop"), respond:

"Stack removal is not supported in this version. To change the stack set, delete `scripts/deploy.mk` and re-compose from the base pattern with `/ipa.compose {pattern-name}`."

Do NOT proceed with any composition or artifact modification.

---

### Step 0.6: Merge New Stacks into Existing Composition

This step takes the parsed existing composition (from Step 0.3a) and the list of new stacks (from Step 0.1) and produces a merged composition. It runs for **add-stacks** and **add-pattern** modes.

#### 0.6.0: Expand Pattern to Stacks (add-pattern mode only)

If the composition mode is **add-pattern**, expand the new pattern into individual stacks before proceeding with the merge:

1. **Read the pattern definition**: Read `patterns/{pattern-name}/PATTERN.md` from the patterns directory (relative to this SKILL.md).

2. **Extract Stack Sequence**: Parse the `## Stack Sequence` section to get the ordered list of `ipa.stack.{service}` references. Each entry becomes a new stack to merge, as if the builder had typed each stack name individually.

3. **Preserve intra-pattern wiring**: Read the `## Wiring` section from `PATTERN.md`. These wiring declarations are **authoritative** for connections between the new pattern's own stacks — they override auto-inference in Step 0.7. Store them separately as `pattern_wiring` for use in Step 0.7.2.

4. **Read ARCHITECTURE.md**: Read `patterns/{pattern-name}/ARCHITECTURE.md`. This content will be added as a new architecture section in the runbook (see RUNBOOK_TEMPLATE.md "Added Pattern" template).

5. **Read Known Deferrals** (optional): If the pattern defines Known Deferrals, store them for inclusion in the security disposition register (Step 10).

6. **Merge the expanded stacks**: Replace the pattern argument with the expanded list of individual stacks. If the builder also provided extra stack names alongside the pattern (add-mixed mode), append those to the expanded list.

After expansion, the remainder of Step 0.6 (validation, metadata, ordering) treats all stacks identically regardless of whether they came from a pattern or were specified individually.

#### 0.6.1: Validate New Stack Skills

For each new stack `ipa.stack.{name}` in the add list:

1. **Check skill exists**: Verify `.claude/skills/ipa.stack.{name}/SKILL.md` exists on disk.
   - If missing: ERROR — "Stack skill `ipa.stack.{name}` not found at `.claude/skills/ipa.stack.{name}/SKILL.md`."

2. **Check suffix uniqueness**: Extract the service suffix from the stack skill's CloudFormation Contract section. Compare against all existing stack suffixes in the current composition.
   - If duplicate suffix found: ERROR — "Cannot add `ipa.stack.{name}` — suffix `{suffix}` already exists in the current composition."

3. **Check already composed**: If the exact stack name (not just suffix) already appears in the existing composition's stack list:
   - Report: "`ipa.stack.{name}` is already composed in the current deployment. Skipping."
   - Remove this stack from the add list and continue with remaining stacks.

If all new stacks are skipped (all already composed), report "All requested stacks are already in the composition. No changes needed." and exit without modifying any files.

#### 0.6.2: Read New Stack Metadata

For each validated new stack, read `.claude/skills/ipa.stack.{name}/SKILL.md` and extract:

| Section | Extract | Purpose |
|---------|---------|---------|
| CloudFormation Contract | Service suffix, template path, capabilities | Stack naming, deploy target |
| Parameters | Parameter name, type, description, required flag | Wiring targets |
| Outputs | Output name, description | Wiring sources |
| Build Requirements (optional) | Type, command | build.mk targets |
| Known Deferrals (optional) | Deferral entries | Security disposition |

Store the extracted metadata alongside the existing composition's stack data.

#### 0.6.3: Compute Merged Deployment Order

Build the merged deployment order:

1. **Start with existing order**: All stacks from the current composition retain their position in the deployment sequence.
2. **Append new stacks**: New stacks are added after all existing stacks.
3. **Respect dependencies**: If a new stack declares dependencies (in its skill's CloudFormation Contract or the pattern's Wiring section), ensure those dependencies appear before it in the order.
   - Dependencies on existing stacks: already satisfied (existing stacks come first).
   - Dependencies between new stacks: order the new stacks so dependencies come first.
   - If a new stack depends on another new stack that is not in the add list: ERROR — "Stack `ipa.stack.{name}` depends on `ipa.stack.{dep}`, which is neither in the existing composition nor being added."

4. **Detect circular dependencies**: After ordering, verify no circular dependency exists among the new stacks. If found: ERROR — "Circular dependency detected: {stack-a} → {stack-b} → ... → {stack-a}."

**Prepare classification for merged stacks**: If a new stack is being added from a pattern (Step 0.6.0) and that pattern's Stack Sequence marks the stack as `(prepare)`, the stack retains its prepare classification in the merged composition. The prepare classification affects which Makefile the stack's target appears in (prepare.mk vs deploy.mk) but does NOT affect the merge ordering logic — prepare stacks are ordered among themselves, deploy stacks among themselves.

#### 0.6.4: Compute Merged Teardown Order

The teardown order is the exact reverse of the merged deployment order. Compute it by reversing the full deploy order list from Step 0.6.3.

#### 0.6.5: Assemble Merged Composition

Combine into a single merged composition record:

- **base_pattern**: The original base pattern name (from Step 0.3a)
- **additions**: Append the new stack/pattern names to the existing additions list
- **all_stacks**: Existing stacks (unchanged) + new stacks (with extracted metadata)
- **deploy_order**: Merged deployment order from Step 0.6.3
- **teardown_order**: Merged teardown order from Step 0.6.4
- **existing_wiring**: All wiring entries from the parsed deploy.mk (unchanged)
- **new_stacks_pending_wiring**: List of new stacks whose parameters need wiring resolution in Step 0.7

Proceed to Step 0.7 for wiring resolution.

---

### Step 0.7: Resolve Wiring for New Stacks

This step auto-infers connections between new stacks' parameters and existing stacks' outputs, presents the proposed wiring to the builder for confirmation, and handles unresolved parameters.

#### 0.7.1: Identify Wirable Parameters

For each new stack (from Step 0.6.5 `new_stacks_pending_wiring`), iterate its Parameters table. **Exclude** these standard parameters from wiring (they are set from `.env`, not from other stacks):
- `Namespace` (always `$(APP_NAMESPACE)`)
- `Environment` (always `$(APP_ENV)`)

All remaining parameters are **wirable** — they may receive their value from another stack's output.

#### 0.7.2: Auto-Infer Wiring (Exact Name Match)

For each wirable parameter on each new stack:

1. **Check intra-pattern wiring first** (add-pattern mode only): If the new stacks came from a pattern expansion (Step 0.6), check the pattern's declared Wiring section. If this parameter has an explicit wiring entry, use it — pattern-declared wiring is authoritative and overrides auto-inference.

2. **Search all stacks' Outputs**: Search the Outputs tables of **all** stacks (both existing and newly added) for an output whose name exactly matches the parameter name.

3. **Match outcomes**:
   - **Exactly one match**: Auto-wire. Record: `{source_suffix, source_output_key, target_suffix, target_parameter, match_type: "auto"}`.
   - **Multiple matches**: Disambiguation required. Record all matches and flag for builder selection in Step 0.7.3.
   - **No match**: Mark as unresolved. Record: `{target_suffix, target_parameter, description, match_type: "unresolved"}`.

#### 0.7.3: Disambiguate Multi-Match Parameters

For each parameter with multiple matching outputs, present the options to the builder:

```
Multiple sources found for {target_stack}.{parameter_name}:

  1. {source_stack_1}.{output_name} — {output_description}
  2. {source_stack_2}.{output_name} — {output_description}
  ...
  S. Skip — leave unresolved

Select source (enter number, or S to skip):
```

Record the builder's selection: `{source_suffix, source_output_key, target_suffix, target_parameter, match_type: "builder-selected"}`. If skipped, mark as unresolved.

#### 0.7.4: Present Wiring Proposal

Display the complete wiring proposal for all new stacks:

```
Wiring for new stacks:

  Source          Output           → Target       Parameter        Match
  ──────          ──────             ──────        ─────────        ─────
  {sfx1}          {output}         → {new_sfx}    {param}          auto
  {sfx2}          {output}         → {new_sfx}    {param}          builder
  (unresolved)    ???              → {new_sfx}    {param}          ???

  {N} auto-detected, {N} builder-selected, {N} unresolved.

  (a) Accept as-is — proceed with current wiring (unresolved params get no value)
  (b) Edit connections — re-wire specific parameters
  (c) Cancel — abort composition
```

#### 0.7.5: Handle Builder Response

- **Accept (a)**: Proceed. If unresolved parameters remain, they will be included as warnings in the runbook (per clarification Q1: partial wiring is allowed).
- **Edit (b)**: For each parameter the builder wants to re-wire:
  - Display available outputs from all stacks
  - Let the builder select a source or mark as unresolved
  - Re-display the updated wiring proposal and confirm again
- **Cancel (c)**: Exit — "Composition cancelled. No files were written."

#### 0.7.6: Finalize Wiring

Combine all wiring entries into the merged composition:

- **Existing wiring** (from Step 0.3a parse): unchanged
- **New auto-detected wiring**: from Step 0.7.2
- **New builder-selected wiring**: from Step 0.7.3
- **Unresolved parameters**: stored separately for runbook warnings

For each new wiring entry, compute the Make variable name: convert the output key to `UPPER_SNAKE_CASE` (e.g., `RepositoryUri` → `REPOSITORY_URI`).

Run validation procedure V5 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

Proceed to Phase 2 (Confirm) — the merged composition with resolved wiring is the input for artifact generation in Steps 6-10.

---

### Phase 0 Routing Summary

Two execution paths converge at Phase 2 (Confirm) → Phase 3 (Generate):

- **Fresh compose / Pattern discovery**: Phase 0 Steps 0.1-0.3 → skip to **Phase 1** (Validate) → Steps 1-4 read pattern and stack skills → Phase 2 (Confirm) → Phase 3 (Generate) → Phase 4 (Report). All existing behavior is unchanged.
- **Add stacks / Add pattern / Idempotent refresh**: Phase 0 Steps 0.1-0.3 → Step 0.3a (parse deploy.mk) → Step 0.4 (confirm) → Step 0.6 (merge) → Step 0.7 (wiring) → skip Phase 1 → **Phase 2** (Confirm, with V5 validation) → Phase 3 (Generate) → Phase 4 (Report).
- **Stacks without pattern** (no deploy.mk + stack args): ERROR in Step 0.3 — no further processing.

Both paths feed the same artifact generation pipeline (Steps 6-10). The only difference is the input source: pattern definition vs. merged composition.

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

To determine stack count for the menu, quickly scan each pattern's `## Stack Sequence` section and count `ipa.stack.*` references.

Store the selected pattern name and directory path.

---

### Step 3: Read Pattern Definition

Read the selected pattern's files from `patterns/{name}/`:

#### 3.1 PATTERN.md

Extract these sections:

- **Stack Sequence**: Numbered list of `ipa.stack.{service}` references with dependency declarations. Extract: stack names, deployment order, dependencies, and **lifecycle classification**.
  - **Parse `(prepare)` annotation**: The `(prepare)` token is optional and appears between the stack skill name and the em-dash description separator. Match pattern: `ipa.stack.{service}\s*(\(prepare\))?\s*—`. If `(prepare)` is present, set `lifecycle = "prepare"` for that stack; otherwise set `lifecycle = "deploy"`. This classification determines which Makefile receives the stack's targets (prepare.mk vs deploy.mk).
- **Teardown Sequence**: Reverse-order list for teardown targets. Note: prepare-classified stacks are excluded from the Teardown Sequence — their teardown targets live in prepare.mk.
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

**Input source**: This step receives composition data from one of two paths:
- **Fresh compose** (Phase 1 flow): Stack list, wiring, and deployment order come from the pattern definition (Steps 3-4).
- **Merged compose** (Phase 0 flow): Stack list, wiring, and deployment order come from the merged composition (Steps 0.6-0.7). This includes both existing stacks and newly added stacks.

The summary and confirmation logic below is identical regardless of input source.

Validate wiring cross-references before displaying the summary. Run validation procedure V4 from [VALIDATION.md](VALIDATION.md). For merged compositions, also run V5 from [VALIDATION.md](VALIDATION.md). STOP on any failure.

Display a summary of what will be generated. Check if generated artifacts already exist (re-composition scenario).

#### Summary Display

```
Composition Summary: {pattern_name}
Project: {APP_NAMESPACE} | Environment: {APP_ENV} | Region: {AWS_REGION}

Stack Inventory:
  | Stack | Suffix | Template | Lifecycle |
  |-------|--------|----------|-----------|
  | ipa.stack.{svc1} | {sfx1} | infra/cfn/{svc1}.yml | prepare |
  | ipa.stack.{svc2} | {sfx2} | infra/cfn/{svc2}.yml | deploy |
  | ... | ... | ... | ... |

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
  - scripts/prepare.mk                          (prepare Makefile — always generated)
  - scripts/deploy.mk
  - scripts/build.mk
  - scripts/test.mk
  - docs/infra/runbook.md
  - docs/infra/security-disposition.md
```

**For merged compositions**, also display:
- Which stacks are existing vs. newly added (mark new stacks with `(new)` in the inventory)
- Unresolved wiring parameters, if any: "**Warning**: {N} parameter(s) unresolved — will appear as warnings in the runbook."

If existing artifacts are detected, add: "**Re-composition**: Existing artifacts will be overwritten. Custom dispositions in security-disposition.md will be preserved."

Ask: "Generate these artifacts? (yes to proceed, no to cancel):"

- **If confirmed**: proceed to artifact generation.
- **If declined**: exit — "Composition cancelled. No files were written."

---

## Phase 3: Generate

### Step 6: Generate deploy.mk

**Input**: The full composition — either from a fresh pattern (Phase 1) or a merged composition (Phase 0). The generation logic below is identical regardless of input source.

**Before generating deploy.mk**, filter the stack list: include only stacks with `lifecycle = "deploy"`. Stacks with `lifecycle = "prepare"` are excluded from deploy.mk entirely — they appear in prepare.mk (generated in Step 6a). This filtering affects the aggregate `deploy:` target, per-stack `deploy-{suffix}` targets, the aggregate `teardown:` target, per-stack `teardown-{suffix}` targets, and the `.PHONY` declaration.

Create `scripts/` directory if it does not exist. Write `scripts/deploy.mk`.

Load [MAKEFILE_TEMPLATES.md](MAKEFILE_TEMPLATES.md) for exact syntax patterns. Generate:

1. **Header**: Comment block with usage instructions, `-include .env`, `.PHONY` declarations.
   - **Fresh compose**: Use the standard header format from MAKEFILE_TEMPLATES.md.
   - **Merged compose**: Use the merged composition header format from MAKEFILE_TEMPLATES.md, including the `# Base: {name} | Added: {list} ({date})` metadata line.
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
   - For wiring entries between prepare stacks: add `$(eval)` lines.
   - Write the `uv run --project utils deploy cfn` command.
   - Add `--capabilities CAPABILITY_NAMED_IAM` if required.
4. **Aggregate teardown target**: `teardown-prepare: teardown-{sfxN} ... teardown-{sfx1}` in reverse order.
5. **Per-stack teardown targets**: `uv run --project utils deploy cfn-delete --stack-name $(APP_NAMESPACE)-$(APP_ENV)-{suffix}`.

**Critical rules**:
- Same naming/variable conventions as deploy.mk
- All targets are `.PHONY`
- Teardown is in exact reverse of prepare deployment order
- Teardown comment: `# === TEARDOWN (manual only — never auto-deleted by /ipa.destroy) ===`

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

**For merged compositions**, also generate these additional sections using the templates in [RUNBOOK_TEMPLATE.md](RUNBOOK_TEMPLATE.md):
- **Added Stacks**: Under the architecture section, append a subsection for each incrementally added stack (stack description from skill, added-on date).
- **Unresolved Wiring (Action Required)**: If any parameters remain unresolved from Step 0.7, insert a warning table listing each unresolved parameter with resolution guidance.

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
5. **For merged compositions**: Also include Known Deferrals from any newly added stack skills. Append these after the base pattern's deferrals with sequential DEF-IDs.
6. Write the new file: header + regenerated Pattern Deferrals (base + added) + preserved Custom Dispositions content.

---

## Phase 4: Report

### Step 11: Completion Report

Display a structured report:

```
Composition Complete: {pattern_name}

Generated artifacts:
  ✓ scripts/prepare.mk                         (prepare Makefile — run once)
  ✓ scripts/deploy.mk                          (deployment Makefile)
  ✓ scripts/build.mk                           (build Makefile)
  ✓ scripts/test.mk                            (test Makefile)
  ✓ docs/infra/runbook.md                      (customer deployment guide)
  ✓ docs/infra/security-disposition.md          (security disposition register)

Summary:
  Stacks composed: {N} ({N_existing} existing + {N_new} new)
  Wiring entries resolved: {N} ({N_auto} auto + {N_builder} builder-selected)
  Unresolved parameters: {N} (see runbook warnings if > 0)
  Build targets generated: {N}
  CFN templates validated: {N}

Next steps:
  • Review generated artifacts
  • Run `make -f scripts/test.mk test-cfn-lint` to validate templates
  • Run `/ipa.prepare` to deploy one-time prerequisites (ECR, etc.)
  • Run `/ipa.security` to update IAM roles for new stacks (if stacks were added)
  • Run `/ipa.deploy` to deploy the composed pattern
```

**Note**: For fresh compose, the summary omits the existing/new breakdown and shows total stacks only.
