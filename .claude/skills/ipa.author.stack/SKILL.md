---
name: ipa-author-stack
description: "Create or update an IPA stack skill — from single-service prepare stacks to multi-service tier stacks — with optional pattern definition authoring. Use when the user says 'create a stack', 'new stack', 'add [service] to IPA', 'create a pattern', 'create a tier', 'create a feature stack', 'write a stack skill', 'update the [service] stack', or wants to add infrastructure to the IPA system. Do NOT use for composing/deploying existing patterns (that is ipa.compose/ipa.deploy)."
---

# ipa.author.stack

Create or update IPA stack skills and pattern definitions. Handles the full spectrum of infrastructure authoring: single-service prepare stacks (ECR, Cognito), multi-service tier stacks (backend, frontend, queue), and pattern definitions (PATTERN.md + ARCHITECTURE.md) — all from one entry point.

**Combined mode is the default.** Most new stacks are tier stacks that also need a pattern definition. Single-service mode is the exception for prepare stacks.

## User Input

```text
$ARGUMENTS
```

Expected: `[create|update] [name]` — e.g., `create ml-pipeline`, `update backend`, `create ecr`.
If mode is omitted, infer from file state.
If name is omitted, ask the user.

## Pre-Execution Checks

1. Read [REFERENCE.md](REFERENCE.md) for structural contracts and conventions. Keep it in context throughout — all sections are needed during authoring.

2. Detect authoring mode from user input and file state:

   | Signal | Mode |
   |--------|------|
   | "create a tier", "create a feature", multi-service scenario, names a pattern concept (e.g., "ml-pipeline") | **Combined** (DEFAULT) |
   | "create a prepare stack", names one AWS service (ECR, SNS, RDS, SES) | **Single-service** |
   | "create a pattern", "define a pattern", referenced stacks already exist | **Pattern-only** |
   | Target stack/pattern files already exist | **Update** (of whichever mode applies) |

   **Combined mode is the default.** Most new stacks are tier stacks that also need a pattern definition. Only use single-service mode when the user explicitly requests a prepare stack or names a single AWS service with no pattern context.

3. Confirm the detected mode with the user:
   "I'll create a [tier stack with pattern definition / single-service prepare stack / pattern definition]. Does that match your intent?"

4. Mode-specific pre-checks:
   - **Single-service / Combined**: If `.claude/skills/ipa.stack.{service}/SKILL.md` exists -> **update** mode. Verify service name does not collide with existing stacks (REFERENCE.md Section 9).
   - **Pattern-only / Combined**: If `.claude/skills/ipa.compose/patterns/{name}/PATTERN.md` exists -> **update** mode. Verify pattern name does not collide with existing patterns.
   - **Update**: Read all existing files in the target directories. Note which files exist and which are absent — absent files will be created.

5. Scan available stack skills: list directories matching `.claude/skills/ipa.stack.*/` and confirm each has a SKILL.md.

## Execution Steps

### Phase 1: Gather Requirements

> **Applies to:** All modes

6. Collect the following from the user, one question at a time. For **update** mode, pre-populate answers from existing files and ask only about changes. Skip questions that don't apply to the detected mode.

   a. **Architecture overview** — "What does this stack/pattern deploy, and what is its role in the architecture?"
      Example: "An ML pipeline with SageMaker endpoints, S3 model storage, and a queue for batch inference jobs"

   b. **Stack selection** (Combined, Pattern-only) — "Which stack skills should this pattern include?" Present the available stack inventory from REFERENCE.md Section 13 as a numbered list, with tier stacks listed first (recommended).
      - **Recommend tier stacks** (backend, frontend, queue) for new patterns.
      - Only suggest individual service stacks for edge cases not covered by tier stacks.

   c. **AWS service and key resources** (Single-service, Combined) — "What AWS service does this stack deploy?" and "What CloudFormation resource types will the template create?"

   d. **Parameters** (Single-service, Combined) — For each parameter beyond Namespace and Environment, collect:
      - Name, Type, Default value, Validation pattern or allowed values, Error message
      - Classification: Configuration, Wirable — Required, Wirable — Optional, or Pattern-provided (see REFERENCE.md Section 5)
      - For Wirable parameters: which upstream stack and output provides the value

   e. **Feature flags** (Combined with tier stacks) — "Which feature flags should be enabled?" Feature flags control conditional resources within tier stacks (e.g., DynamoDB tables, SQS integration). Defaults are `false` — patterns must explicitly enable them.
      Example: Backend with `EnablePassengersTable=true`, Queue with `EnableJobsTable=true`

   f. **Outputs** (Single-service, Combined) — For each output, collect:
      - Name, Description
      - Used By: which downstream stacks or operational steps consume it

   g. **Capabilities** (Single-service, Combined) — Does the template create IAM resources?
      - If yes -> `CAPABILITY_NAMED_IAM`
      - If no -> `none`

   h. **Stack name suffix** (Single-service, Combined) — Confirm suffix for `{APP_NAMESPACE}-{APP_ENV}-{suffix}`. Default: service name.

   i. **Multi-instance support** (Single-service) — Can this stack be deployed multiple times with different suffixes?

   j. **Build requirements** (Single-service, Combined) — Does this stack need a pre-built artifact (container image, frontend bundle)?

   k. **Security posture** (Single-service, Combined) — Collect:
      - Deployment IAM actions, Runtime permissions, Security controls, Known deferrals

   l. **Lifecycle classification** (Combined, Pattern-only) — For each selected stack: prepare or deploy?

   m. **Dependency graph** (Combined, Pattern-only) — For each stack, ask: "What does this stack depend on?"

   n. **Config overrides** (Combined, Pattern-only) — Non-default parameter values for each stack.

   o. **Post-deploy steps** (Combined, Pattern-only) — Operational steps after all stacks deploy.

7. Present a summary of what will be created/updated and confirm before proceeding.

### Phase 2: Create CloudFormation Template

> **Applies to:** Single-service, Combined

8. Create directory `infra/cfn/{service}/` if it does not exist.

9. Write `infra/cfn/{service}/{service}.yml` following the CloudFormation Template Skeleton in REFERENCE.md Section 4:
   - Namespace and Environment parameters with the standard AllowedPattern (copy exactly from REFERENCE.md).
   - Service-specific parameters with appropriate AllowedPattern, AllowedValues, and ConstraintDescription.
   - Conditions section if any Wirable — Optional parameters exist.
   - Resources with `!Sub` for dynamic naming using `${Namespace}` and `${Environment}`.
   - Tags on every taggable resource (at minimum: `Environment`).
   - Outputs exported via `Export: Name: !Sub '${AWS::StackName}-{OutputKey}'`.
   - For tier stacks: include `Enable*` feature flag parameters with Conditions, defaulting to `false`.

10. Validate the template:
    ```
    aws cloudformation validate-template --template-body file://infra/cfn/{service}/{service}.yml
    ```
    - If validation succeeds -> proceed.
    - If validation fails -> fix and re-validate (max 3 iterations).
    - If still failing -> stop and report the validation error.

### Phase 3: Create Stack Skill Files

> **Applies to:** Single-service, Combined

11. Create directory `.claude/skills/ipa.stack.{service}/` if it does not exist.

12. Write `.claude/skills/ipa.stack.{service}/SKILL.md` following REFERENCE.md Section 1. Every section is mandatory except Build Requirements and Naming Convention (include only when applicable):
    - Frontmatter: `name: ipa-stack-{service}`, `description: "{one sentence}"`
    - H1 title and summary paragraph
    - CloudFormation Contract (Template, Stack name, Capabilities)
    - Parameters table (Namespace and Environment first, with exact validation from REFERENCE.md)
    - Parameter Classification subsection
    - Outputs table
    - For tier stacks: Feature Flags table and Wirable Parameters table
    - Build Requirements (only if applicable)
    - Naming Convention (only if applicable)
    - Security Summary with links to SECURITY.md

13. Write `.claude/skills/ipa.stack.{service}/SECURITY.md` following REFERENCE.md Section 2.

14. Write `.claude/skills/ipa.stack.{service}/TROUBLESHOOT.md` following REFERENCE.md Section 3.

### Phase 4: Create Pattern Definition

> **Applies to:** Combined, Pattern-only

15. Order the selected stacks into a deployment sequence:
    - Prepare stacks first (no deploy-stack dependencies).
    - Deploy stacks in dependency order.
    - Stacks at the same dependency level get sequential numbers or parallel notation.

16. Derive the Teardown Sequence: reverse of deploy-lifecycle stacks only.

17. Define wiring:

    **ultrathink** — Shallow wiring analysis produces broken Makefiles. Trace every wirable parameter through the dependency graph.

    a. Read each selected stack's SKILL.md to extract Parameters, Parameter Classification, Outputs, Feature Flags, and Wirable Parameters tables.
    b. Note internal connections within tier stacks — these do NOT need wiring entries.
    c. For each Wirable parameter in a target stack, find the source:
       - Tier stacks pre-document expected sources in their Wirable Parameters table.
       - Check if a source stack exports a matching output.
       - For Wirable — Optional parameters: wire only if the source stack is in the pattern.
       - For feature-flag-gated parameters: wire only when the feature flag is enabled.
    d. Present the wiring summary to the user for confirmation.

18. Collect Known Deferrals from each stack's SECURITY.md.

19. Collect Post-Deploy steps if identified in Phase 1.

20. Create directory `.claude/skills/ipa.compose/patterns/{name}/` if it does not exist.

21. Write `.claude/skills/ipa.compose/patterns/{name}/PATTERN.md` following REFERENCE.md Section 10.

22. Write `.claude/skills/ipa.compose/patterns/{name}/ARCHITECTURE.md` following REFERENCE.md Section 11.

### Phase 5: Validate

> **Applies to:** All modes (validates only artifacts created in this session)

**ultrathink** — Shallow validation means the skill ships with inconsistencies that only surface at compose or deploy time.

23. **Stack validation** (Single-service, Combined):
    - Every parameter in SKILL.md Parameters table exists in the CFN template with matching name, type, and validation.
    - Every output in SKILL.md Outputs table exists in the CFN template with matching export name.
    - Every IAM action in SECURITY.md corresponds to a resource type in the CFN template.
    - Parameter Classification matches actual parameter sources.
    - If template uses `CAPABILITY_NAMED_IAM`, CloudFormation Contract says so (and vice versa).

24. **Compose compatibility** (Single-service, Combined):
    - SKILL.md has all four required sections with exact heading names: `## CloudFormation Contract`, `## Parameters`, `### Parameter Classification`, `## Outputs`.
    - Parameter table columns: Parameter, Type, Default, Validation, Error Message.
    - Output table columns: Output, Description, Export Convention, Used By.
    - Wirable parameters use the `<-` arrow notation in Parameter Classification.

25. **Pattern validation** (Combined, Pattern-only):
    - `## Stack Sequence` heading with at least one stack.
    - `## Wiring` heading with YAML code block.
    - `## Teardown Sequence` heading present.
    - ARCHITECTURE.md exists in the pattern directory.
    - Every `source.output` exists in source stack's Outputs table.
    - Every `target.parameter` exists in target stack's Parameters table.
    - No circular dependencies. No forward references in dependency graph.
    - Suffix uniqueness across all stacks in the pattern.
    - Teardown Sequence is exact reverse of deploy-lifecycle stacks.

26. If any validation fails -> fix the issue and re-validate (max 3 iterations). If unable to fix -> document the issue in the completion report.

## Rules

### General
- File paths in SKILL.md use relative paths from project root (e.g., `infra/cfn/{service}/{service}.yml`).
- When updating existing files, preserve content that is not being changed. Do not rewrite unchanged sections.
- In combined mode, create the CFN template and stack skill files (Phases 2-3) before the pattern definition (Phase 4) — the pattern references the stack skill.

### Stack Rules
- Namespace and Environment parameters are mandatory in every CFN template with the exact AllowedPattern from REFERENCE.md Section 4. No exceptions.
- All CFN outputs must use `Export: Name: !Sub '${AWS::StackName}-{OutputKey}'`.
- SKILL.md frontmatter `name` is kebab-case: `ipa-stack-{service}`.
- Stack name suffix defaults to the service name unless the user specifies otherwise.
- Never create IAM resources without setting Capabilities to `CAPABILITY_NAMED_IAM`.
- Every Known Deferral must have a Reason and Risk assessment.
- The CFN template directory name and the SKILL.md template path must be consistent: `infra/cfn/{service}/{service}.yml`.

### Pattern Rules
- Pattern names are lowercase with hyphens (e.g., `react-rest-lambda`, `ml-pipeline`).
- Only reference stack skills that exist in `.claude/skills/ipa.stack.*/`.
- **Prefer tier stacks** (backend, frontend, queue) over individual service stacks for new patterns.
- **Feature flags default to `false`**. Patterns must explicitly enable them via Config.
- **Deploy ordering for queue + backend**: Queue deploys before backend. Backend receives queue outputs via wirable parameters and requires `EnableSqsIntegration=true`.
- Stack Sequence must satisfy topological ordering — no forward references.
- Teardown Sequence must be the exact reverse of deploy-lifecycle stacks.
- Wiring references use stack suffixes (not full `ipa.stack.{service}` names).
- **Internal tier connections** do not need wiring entries — document as YAML comments.
- Convention-based connections are documented as YAML comments, not wiring entries.
- Known Deferral IDs use `{STACK_PREFIX}-{N}` format, unique within the pattern.
- Post-Deploy steps that update existing stacks must pass ALL original parameters.

## Completion Report

Adapts to the mode — include only sections for artifacts created in this session.

**Created/Updated:**
- Template: `infra/cfn/{service}/{service}.yml` *(Single-service, Combined)*
- Skill: `.claude/skills/ipa.stack.{service}/SKILL.md` *(Single-service, Combined)*
- Security: `.claude/skills/ipa.stack.{service}/SECURITY.md` *(Single-service, Combined)*
- Troubleshoot: `.claude/skills/ipa.stack.{service}/TROUBLESHOOT.md` *(Single-service, Combined)*
- Pattern: `.claude/skills/ipa.compose/patterns/{name}/PATTERN.md` *(Combined, Pattern-only)*
- Architecture: `.claude/skills/ipa.compose/patterns/{name}/ARCHITECTURE.md` *(Combined, Pattern-only)*

**Stack Summary** *(Single-service, Combined)*:
- Parameters: {count} ({config} configuration, {wirable_req} wirable-required, {wirable_opt} wirable-optional)
- Outputs: {count} exported
- Capabilities: {none or CAPABILITY_NAMED_IAM}

**Pattern Summary** *(Combined, Pattern-only)*:
- Stacks: {total} ({prepare_count} prepare, {deploy_count} deploy)
- Wiring entries: {count} ({auto_count} auto-wirable, {explicit_count} explicit)
- Known deferrals: {count}
- Post-deploy steps: {count}

**Next steps:**
- Validate template: `aws cloudformation validate-template --template-body file://infra/cfn/{service}/{service}.yml` *(if stack created)*
- Compose the pattern: `/ipa.compose {name}` *(if pattern created)*
- Review generated Makefiles in `scripts/`
- Deploy: `/ipa.deploy`
