# Pre-Composition Validation Procedures

> Reference file for `/ipa.compose` SKILL.md. Loaded on demand during pre-flight and reading steps.
> Contains validation checks that MUST pass before artifact generation.

**Rule**: If any validation fails, STOP immediately. Display the error message and do NOT generate any artifacts.

---

## V1: .env Variable Validation

Read `.env` at the project root. Verify all required IPA variables are present and non-empty:

| Variable | Required By | Error If Missing |
|----------|-------------|------------------|
| `APP_NAMESPACE` | Stack naming | "Missing `APP_NAMESPACE` in `.env`. Run `/ipa.init` first to configure project defaults." |
| `APP_ENV` | Stack naming | "Missing `APP_ENV` in `.env`. Run `/ipa.init` first to configure project defaults." |
| `AWS_REGION` | Runbook | "Missing `AWS_REGION` in `.env`. Run `/ipa.init` first to configure project defaults." |
| `AWS_ACCOUNT_ID` | Runbook | "Missing `AWS_ACCOUNT_ID` in `.env`. Run `/ipa.init` first to configure project defaults." |
| `AWS_PROFILE` | Runbook | "Missing `AWS_PROFILE` in `.env`. Run `/ipa.init` first to configure project defaults." |

If `.env` does not exist at all: "`.env` not found. Run `/ipa.init` first to configure project defaults."

---

## V2: Pattern Validation

For the selected pattern at `patterns/{name}/PATTERN.md` (relative to the compose skill directory):

### V2.2 Stack Sequence Non-Empty

The Stack Sequence must reference at least one stack.

**Error**: "Pattern `patterns/{name}` references zero stacks. A pattern must compose at least one stack."

### V2.3 Required Content

Verify the following content exists for the pattern:

- `## Wiring` section in `PATTERN.md` — structured wiring map
- `ARCHITECTURE.md` file in the pattern directory — architecture diagram and summary

**Error**: "Pattern `patterns/{name}` is missing `{item}`. This is required for composition."

---

## V3: Stack Skill Validation

For each stack referenced in the pattern's Stack Sequence:

### V3.1 Stack Skill Exists

Verify `.claude/skills/ipa.stack.{service}/SKILL.md` exists.

**Error**: "Stack skill `ipa.stack.{service}` not found at `.claude/skills/ipa.stack.{service}/SKILL.md`. This stack is referenced by pattern `patterns/{name}` in step {N} of the Stack Sequence."

### V3.2 Required Sections

Verify these sections exist in the stack SKILL.md:

- `## CloudFormation Contract` — must include Template path and service suffix
- `## Parameters` — parameter table
- `## Outputs` — output table

**Error**: "Stack skill `ipa.stack.{service}` is missing required section `{section}`."

### V3.3 CloudFormation Template Exists

Extract the template path from the stack's CloudFormation Contract section. Resolve to the expected filesystem path (typically `infra/cfn/{service}.yml`).

Verify the template file exists on disk.

**Error**: "CloudFormation template `{path}` not found on disk. This template is referenced by stack skill `ipa.stack.{service}`."

### V3.4 Service Suffix Uniqueness

Collect all service suffixes from all stacks in the pattern. Verify no two stacks share the same suffix.

**Error**: "Service suffix collision: stacks `ipa.stack.{service1}` and `ipa.stack.{service2}` both use suffix `{suffix}`. Each stack must have a unique service suffix."

---

## V4: Wiring Map Validation

Read the `## Wiring` section from the pattern's `PATTERN.md` and validate each wiring entry:

### V4.1 Source Output Exists

For each wiring entry, verify `source.output` exists in the source stack skill's `## Outputs` table.

**Error**: "Wiring error: output `{output}` does not exist in stack `ipa.stack.{source}` Outputs table. Check PATTERN.md ## Wiring section entry: `{source}.{output}` → `{target}.{parameter}`."

### V4.2 Target Parameter Exists

For each wiring entry with `target.parameter`, verify it exists in the target stack skill's `## Parameters` table.

**Error**: "Wiring error: parameter `{parameter}` does not exist in stack `ipa.stack.{target}` Parameters table. Check PATTERN.md ## Wiring section entry: `{source}.{output}` → `{target}.{parameter}`."

### V4.3 Exactly One Target

Each wiring entry must have exactly one of `target.parameter` or `target.env`.

**Error**: "Wiring error: entry `{source}.{output}` must specify exactly one of `target.parameter` or `target.env`, not both or neither."

### V4.4 No Circular Dependencies

Verify the dependency graph (derived from wiring) has no cycles.

**Error**: "Circular dependency detected: {cycle_description}. The Stack Sequence must form a directed acyclic graph."

---

## V5: Merge Validation

After merging new stacks or patterns into an existing composition, validate the merged result before generating artifacts. These checks operate on the **combined** composition (base + additions).

### V5.1 No Duplicate Suffixes Across Base + Additions

Collect all service suffixes from the base composition (parsed from `deploy.mk`) and from each new stack being added. Verify no suffix appears more than once across the combined set.

**Check**: For every stack in (base stacks + new stacks), extract the service suffix from its CloudFormation Contract. Confirm all suffixes are unique.

**Error**: "Merge conflict: service suffix `{suffix}` is used by existing stack `ipa.stack.{existing_service}` and new stack `ipa.stack.{new_service}`. Each stack must have a unique service suffix across the entire composition."

### V5.2 No Circular Dependencies in Merged Wiring Graph

Build the full dependency graph from the merged wiring (base wiring + new wiring entries). Verify the graph contains no cycles.

**Check**: Construct a directed graph where each edge represents a wiring dependency (source stack → target stack). Perform a topological sort. If the sort fails, a cycle exists.

**Error**: "Circular dependency detected in merged composition: {cycle_description}. Adding `{new_stacks}` introduces a cycle in the deployment order. Review the wiring between base and new stacks."

### V5.3 All Wired Source Outputs Exist in Stack Skills

For every wiring entry in the merged wiring map, verify the source output name exists in the source stack skill's `## Outputs` table.

**Check**: For each wiring entry `{source}.{output} → {target}.{parameter}`, read `ipa.stack.{source}` SKILL.md and confirm `{output}` appears in its `## Outputs` table.

**Error**: "Merge wiring error: output `{output}` does not exist in stack `ipa.stack.{source}` Outputs table. This wiring entry was produced during merge of `{new_stacks}` into the existing composition."

### V5.4 All Wired Target Parameters Exist in Stack Skills

For every wiring entry in the merged wiring map, verify the target parameter name exists in the target stack skill's `## Parameters` table.

**Check**: For each wiring entry `{source}.{output} → {target}.{parameter}`, read `ipa.stack.{target}` SKILL.md and confirm `{parameter}` appears in its `## Parameters` table.

**Error**: "Merge wiring error: parameter `{parameter}` does not exist in stack `ipa.stack.{target}` Parameters table. This wiring entry was produced during merge of `{new_stacks}` into the existing composition."

### V5.5 All Referenced Stack Skills Exist on Disk

Verify that every stack referenced in the merged composition (base + additions) has a corresponding skill directory and SKILL.md on disk.

**Check**: For each stack `ipa.stack.{service}` in the merged stack list, confirm `.claude/skills/ipa.stack.{service}/SKILL.md` exists.

**Error**: "Stack skill `ipa.stack.{service}` not found at `.claude/skills/ipa.stack.{service}/SKILL.md`. This stack is referenced in the merged composition (base + additions). Ensure the stack skill is installed before composing."

### V5.6 All Referenced CloudFormation Templates Exist on Disk

Verify that every CloudFormation template referenced by stacks in the merged composition exists on disk.

**Check**: For each stack `ipa.stack.{service}` in the merged stack list, extract the template path from its CloudFormation Contract section (typically `infra/cfn/{service}.yml`). Confirm the file exists.

**Error**: "CloudFormation template `{path}` not found on disk. This template is referenced by stack `ipa.stack.{service}` in the merged composition. Ensure the template exists before composing."
