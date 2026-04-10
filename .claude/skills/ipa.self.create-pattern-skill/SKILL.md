---
name: ipa-self-create-pattern-skill
description: "Create or update an IPA deployment pattern that composes stack skills into a dependency-ordered, wired deployment graph. Use when the user says 'create a pattern', 'new pattern', 'define a pattern', 'write a pattern for [name]', 'update the [name] pattern', 'compose stacks into a pattern', 'design a deployment pattern', or wants to define a reusable architecture from existing ipa.stack.* skills. Do NOT use for composing/deploying an existing pattern (that is ipa.compose and ipa.deploy) or for creating individual stack skills (that is ipa.self.create-stack-skill)."
---

# ipa.self.create-pattern-skill

Create or update an IPA deployment pattern — the PATTERN.md and ARCHITECTURE.md files that define how stack skills compose into a deployable architecture. The output is consumed by `ipa.compose` to generate Makefiles.

## User Input

```text
$ARGUMENTS
```

Expected: `[create|update] [pattern-name]` — e.g., `create api-worker-queue`, `update react-rest-lambda`.
If mode is omitted, infer from whether `.claude/skills/ipa.compose/patterns/{name}/PATTERN.md` exists.
If pattern-name is omitted, ask the user.

## Pre-Execution Checks

1. Read [REFERENCE.md](REFERENCE.md) for structural contracts, templates, and the available stack inventory. Keep it in context throughout.
2. Determine mode:
   - If `.claude/skills/ipa.compose/patterns/{name}/PATTERN.md` exists -> **update** mode.
   - If it does not exist -> **create** mode.
   - If the user explicitly specified a mode that conflicts with file state -> ask: "Pattern already exists. Switch to update mode?" (or vice versa).
3. If mode is **update**: read all existing files in `.claude/skills/ipa.compose/patterns/{name}/`. Note what exists.
4. If mode is **create**: verify pattern name does not collide with existing patterns. List directories in `.claude/skills/ipa.compose/patterns/`.
5. Scan available stack skills: list directories matching `.claude/skills/ipa.stack.*/` and confirm each has a SKILL.md.

## Execution Steps

### Phase 1: Gather Requirements

6. Collect the following from the user. For **update** mode, present current values and ask what's changing.

   a. **Architecture overview** — "What does this pattern deploy end-to-end? What is the user-facing application?"
      Example: "A REST API backed by Lambda with DynamoDB storage, Cognito auth, and a React frontend on CloudFront"

   b. **Stack selection** — "Which stack skills should this pattern include?" Present the available stack inventory from REFERENCE.md Section 4 as a numbered list, with tier stacks listed first (recommended). The user selects by number or name.
      - **Recommend tier stacks** (backend, frontend, queue) for new patterns. These consolidate related services and minimize inter-stack wiring.
      - Only suggest individual service stacks (lambda, apigwv2, s3, etc.) for edge cases not covered by tier stacks.
      - For tier stacks with feature flags, ask which optional resources to enable (see step 6f-ii).

   c. **Lifecycle classification** — For each selected stack, determine: prepare or deploy?
      - Recommend `(prepare)` for: authentication providers, container registries, and other foundational resources that should survive teardown.
      - Default to deploy for all others.

   d. **Dependency graph** — For each stack, ask: "What does this stack depend on?"
      - Pre-populate obvious dependencies from wirable parameters (e.g., Lambda depends on ECR for ImageUri, Cognito for AuthIssuer).
      - Validate that dependencies reference stacks earlier in the sequence.

   e. **Stack suffixes** — Confirm the suffix for each stack. Default to the service name. Flag any collisions.

   f. **Config overrides** — For any stack that needs non-default parameter values, collect them.
      Example: Backend with `FunctionName=fn InvokeMode=RESPONSE_STREAM Timeout=300`

      **Feature flags** — For tier stacks (backend, queue), ask which feature flags to enable. Feature flags control conditional resources within the tier (e.g., DynamoDB tables, SQS integration). Defaults are `false` — patterns must explicitly enable them.
      Example: Backend with `EnablePassengersTable=true`, Queue with `EnableJobsTable=true`

   g. **Post-deploy steps** — "Are there operational steps needed after all stacks deploy?" (e.g., frontend config generation, data loading, CORS updates, Cognito callback wiring).

7. If mode is **update**: present a summary of what will change and confirm before proceeding.

### Phase 2: Build Stack Sequence and Teardown

8. Order the selected stacks into a deployment sequence:
   - Prepare stacks first (they have no deploy-stack dependencies).
   - Deploy stacks in dependency order: stacks with no dependencies first, then stacks that depend on them.
   - Stacks at the same dependency level get sequential numbers or parallel notation (e.g., `5.` and `5a.`).

9. Derive the Teardown Sequence:
   - Take only deploy-lifecycle stacks.
   - Reverse the deployment order exactly.
   - Parallel stacks remain at their reverse position.

### Phase 3: Define Wiring

**ultrathink** — Shallow wiring analysis produces incomplete or incorrect connections that cause `ipa.compose` to generate broken Makefiles. Every wirable parameter needs tracing through the dependency graph.

10. Read each selected stack's SKILL.md to extract:
    - Parameters table and Parameter Classification (identify all Wirable — Required and Wirable — Optional parameters).
    - Outputs table (identify all exported outputs).
    - For tier stacks: also read the Feature Flags table and Wirable Parameters table (which pre-documents expected sources).
    - Note internal connections within tier stacks — these do NOT need wiring entries (e.g., Lambda↔API Gateway, Lambda↔DynamoDB within backend tier are handled by `!GetAtt`/`!Ref` inside the template).

11. For each Wirable parameter in a target stack, find the source:
    - **Tier stacks pre-document their expected sources** in the Wirable Parameters table. Use this as a starting point — it lists the expected source stack and output for each wirable parameter.
    - Check if a source stack in the pattern exports a matching output.
    - When names match exactly (e.g., `BucketArn` output -> `BucketArn` parameter), note as auto-wirable.
    - When names differ (e.g., `IssuerUrl` output -> `AuthIssuer` parameter), the wiring entry must provide the explicit mapping.
    - For Wirable — Optional parameters: wire only if the source stack is included in the pattern. If not, leave unwired (the target stack handles the empty case).
    - For feature-flag-gated parameters (e.g., `SqsQueueUrl` gated by `EnableSqsIntegration`): wire only when the feature flag is enabled in the Config.
    - For unresolved wirable parameters: ask the user which source to use, or confirm the parameter should remain unresolved.

12. Assemble the complete wiring list as source/target/notes entries. Present to the user for confirmation:

    ```
    Wiring Summary:
    | Source Stack | Output | -> Target Stack | Parameter | Type |
    |-------------|--------|-----------------|-----------|------|
    | ecr | RepositoryUri | backend | ImageUri | explicit |
    | cognito | IssuerUrl | backend | AuthIssuer | explicit |
    | cognito | UserPoolClientId | backend | AuthAudience | explicit |
    | security | LogBucketName | frontend | LogBucketDomainName | explicit |

    Internal (no wiring entries needed):
    - backend: Lambda↔API Gateway v2, Lambda↔DynamoDB, Lambda↔CloudWatch
    - frontend: S3↔CloudFront OAC
    ```

    Ask: "Does this wiring look correct? Any connections to add or remove?"

13. Identify convention-based and internal connections. Document these as YAML comments in the Wiring section:
    - **Internal connections** within tier stacks (handled by `!GetAtt`/`!Ref` in the template).
    - **Convention-based connections** (e.g., DynamoDB table names resolved at runtime via `PynamodbUtil.env_table_name()`).

### Phase 4: Collect Deferrals and Post-Deploy

14. **Known Deferrals** — For each stack in the pattern, check its SECURITY.md Known Deferrals table. Collect relevant deferrals that apply at the pattern level (e.g., CORS wildcard during initial deploy, missing WAF). Assign IDs using `{STACK_PREFIX}-{N}` format.

15. **Post-Deploy steps** — If the user identified post-deploy steps in Phase 1:
    - For each step, collect: Action, Script/Command, Dependencies, Stack outputs needed, .env variables needed.
    - Order steps by dependencies.
    - For steps that update existing CloudFormation stacks, note that ALL original parameters must be passed through.

### Phase 5: Create Pattern Files

16. Create directory `.claude/skills/ipa.compose/patterns/{name}/` if it does not exist.

17. Write `.claude/skills/ipa.compose/patterns/{name}/PATTERN.md` following REFERENCE.md Section 1:
    - H1 title with pattern name and description paragraph.
    - Stack Sequence with exact format: numbered list, `(prepare)` annotations, Depends on, Suffix, optional Config.
    - Teardown Sequence: reverse of deploy-lifecycle stacks.
    - Wiring: YAML code block with source/target/notes entries. Include convention-based connections as comments.
    - Known Deferrals: table with ID, Finding, Rationale.
    - Post-Deploy: H3 subsection per step with Action, Script, Depends on, Stack outputs, .env variables, Command, Notes.

18. Write `.claude/skills/ipa.compose/patterns/{name}/ARCHITECTURE.md` following REFERENCE.md Section 2:
    - H1 title and one-sentence description.
    - System Architecture: ASCII layer diagram showing dependency flow.
    - Stack Inventory: table with Stack, Layer, Purpose, Status.
    - Deployment Order: brief description of bottom-up deployment and reverse teardown.
    - Security Model: security principles and documented exceptions.
    - Deployment Assumptions: prerequisites for deploying this pattern.

### Phase 6: Validate

**ultrathink** — Shallow validation here means the pattern ships with missing wiring, invalid dependencies, or structural errors that cause `ipa.compose` to fail at composition time.

19. Validate pattern structure (V2 compatibility):
    - `## Stack Sequence` heading exists with at least one stack.
    - `## Wiring` heading exists with YAML code block.
    - `## Teardown Sequence` heading exists.
    - ARCHITECTURE.md exists in the pattern directory.

20. Validate wiring cross-references (V4 compatibility):
    - Every `source.stack` suffix matches a stack in Stack Sequence.
    - Every `target.stack` suffix matches a stack in Stack Sequence.
    - Every `source.output` exists in the source stack's SKILL.md Outputs table.
    - Every `target.parameter` exists in the target stack's SKILL.md Parameters table.
    - No circular dependencies in the wiring graph.

21. Validate dependency ordering:
    - Every stack's `Depends on:` references only stacks that appear earlier in the sequence.
    - No forward references.
    - Teardown Sequence is exact reverse of deploy-lifecycle stacks in Stack Sequence.
    - Prepare stacks are excluded from Teardown Sequence.

22. Validate stack skill existence:
    - Every `ipa.stack.{service}` referenced in Stack Sequence has a corresponding `.claude/skills/ipa.stack.{service}/SKILL.md`.
    - Every referenced CloudFormation template file exists at the path declared in the stack's CloudFormation Contract.

23. Validate suffix uniqueness:
    - No two stacks in the pattern share the same suffix.

24. If any validation fails -> fix the issue in the affected file(s) and re-validate (max 3 iterations). If unable to fix -> document the issue in the completion report and warn the user.

## Rules

- Pattern names are lowercase with hyphens (e.g., `react-rest-lambda`, `api-worker-queue`).
- Only reference stack skills that exist in `.claude/skills/ipa.stack.*/`. Do not reference stacks that have not been created yet.
- **Prefer tier stacks** (backend, frontend, queue) over individual service stacks for new patterns. Tier stacks consolidate related services and minimize inter-stack wiring. Only use service stacks for edge cases not covered by tier stacks.
- **Feature flags default to `false`** in tier stacks. Patterns must explicitly enable them via Config (e.g., `EnablePassengersTable=true`). Do not assume feature flags are enabled.
- **Deploy ordering for queue + backend**: Queue deploys before backend. Backend receives queue outputs (SqsQueueUrl, SqsSendQueueArns) via wirable parameters and requires `EnableSqsIntegration=true`.
- Stack Sequence must satisfy topological ordering — no stack may depend on a stack that appears after it.
- Teardown Sequence must be the exact reverse of deploy-lifecycle stacks. No reordering.
- Wiring references use stack suffixes (not full `ipa.stack.{service}` names) for both source and target.
- Every Wirable — Required parameter should have a wiring entry unless the user explicitly accepts it as unresolved.
- **Internal tier connections** (Lambda↔API Gateway, Lambda↔DynamoDB, S3↔CloudFront, SQS↔worker Lambda, etc.) do not need wiring entries — they are handled by `!GetAtt`/`!Ref` within the tier template. Document them as YAML comments.
- Convention-based connections are documented as YAML comments in the Wiring section, not as wiring entries.
- Known Deferral IDs use `{STACK_PREFIX}-{N}` format and must be unique within the pattern.
- Post-Deploy steps that update existing CloudFormation stacks must note "passes ALL original parameters plus updated parameter."
- When updating an existing pattern, preserve unchanged sections. Do not rewrite the entire file.

## Completion Report

**Created/Updated:**
- Pattern: `.claude/skills/ipa.compose/patterns/{name}/PATTERN.md`
- Architecture: `.claude/skills/ipa.compose/patterns/{name}/ARCHITECTURE.md`

**Summary:**
- Stacks: {total} ({prepare_count} prepare, {deploy_count} deploy)
- Wiring entries: {count} ({auto_count} auto-wirable, {explicit_count} explicit, {unresolved_count} unresolved)
- Known deferrals: {count}
- Post-deploy steps: {count}

**Next steps:**
- Compose the pattern: `/ipa.compose {name}`
- Review generated Makefiles in `scripts/`
- Deploy prerequisites: `/ipa.prepare`
- Deploy the pattern: `/ipa.deploy`
