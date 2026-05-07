---
name: ipa-author-stack
description: "Create or update an IPA stack skill — from single-service prepare stacks to multi-service tier stacks. Use when the user says 'create a stack', 'new stack', 'add [service] to IPA', 'create a tier', 'create a feature stack', 'write a stack skill', 'update the [service] stack', or wants to add infrastructure to the IPA system. Do NOT use for composing/deploying existing stacks (that is ipa-compose/ipa-deploy)."
---

# ipa-author-stack

Create or update IPA stack skills. Handles the full spectrum of infrastructure authoring: single-service prepare stacks (ECR, Cognito) and multi-service tier stacks (backend, frontend, queue).

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
   | "create a tier", "create a feature", multi-service scenario | **Tier stack** |
   | "create a prepare stack", names one AWS service (ECR, SNS, RDS, SES) | **Single-service** |
   | Target stack files already exist | **Update** |

3. Confirm the detected mode with the user:
   "I'll create a [tier stack / single-service prepare stack]. Does that match your intent?"

4. Mode-specific pre-checks:
   - If `.claude/skills/ipa.stack.{service}/SKILL.md` exists -> **update** mode. Verify service name does not collide with existing stacks (REFERENCE.md Section 9).
   - **Update**: Read all existing files in the target directories. Note which files exist and which are absent — absent files will be created.

5. Scan available stack skills: list directories matching `.claude/skills/ipa.stack.*/` and confirm each has a SKILL.md.

## Execution Steps

### Phase 1: Gather Requirements

> **Applies to:** All modes

6. Collect the following from the user, one question at a time. For **update** mode, pre-populate answers from existing files and ask only about changes.

   a. **Architecture overview** — "What does this stack deploy, and what is its role in the architecture?"
      Example: "A queue tier with SQS, DLQ, worker Lambda, and a jobs DynamoDB table"

   b. **AWS service and key resources** — "What AWS service does this stack deploy?" and "What CloudFormation resource types will the template create?"

   c. **Parameters** — For each parameter beyond Namespace and Environment, collect:
      - Name, Type, Default value, Validation pattern or allowed values, Error message
      - Classification: Configuration, Wirable — Required, Wirable — Optional, or Pattern-provided (see REFERENCE.md Section 5)
      - For Wirable parameters: which upstream stack and output provides the value

   d. **Feature flags** (tier stacks) — "Which feature flags should this stack support?" Feature flags control conditional resources within tier stacks (e.g., DynamoDB tables, SQS integration). Defaults are `false`.
      Example: Backend with `EnablePassengersTable`, Queue with `EnableJobsTable`

   e. **Outputs** — For each output, collect:
      - Name, Description
      - Used By: which downstream stacks or operational steps consume it

   f. **Capabilities** — Does the template create IAM resources?
      - If yes -> `CAPABILITY_NAMED_IAM`
      - If no -> `none`

   g. **Stack name suffix** — Confirm suffix for `{APP_NAMESPACE}-{APP_ENV}-{suffix}`. Default: service name.

   h. **Multi-instance support** (single-service only) — Can this stack be deployed multiple times with different suffixes?

   i. **Build requirements** — Does this stack need a pre-built artifact (container image, frontend bundle)?

   j. **Security posture** — Collect:
      - Deployment IAM actions, Runtime permissions, Security controls, Known deferrals

7. Present a summary of what will be created/updated and confirm before proceeding.

### Phase 2: Create CloudFormation Template

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

### Phase 4: Validate

**ultrathink** — Shallow validation means the skill ships with inconsistencies that only surface at compose or deploy time.

15. **Stack validation**:
    - Every parameter in SKILL.md Parameters table exists in the CFN template with matching name, type, and validation.
    - Every output in SKILL.md Outputs table exists in the CFN template with matching export name.
    - Every IAM action in SECURITY.md corresponds to a resource type in the CFN template.
    - Parameter Classification matches actual parameter sources.
    - If template uses `CAPABILITY_NAMED_IAM`, CloudFormation Contract says so (and vice versa).

16. **Compose compatibility**:
    - SKILL.md has all four required sections with exact heading names: `## CloudFormation Contract`, `## Parameters`, `### Parameter Classification`, `## Outputs`.
    - Parameter table columns: Parameter, Type, Default, Validation, Error Message.
    - Output table columns: Output, Description, Export Convention, Used By.
    - Wirable parameters use the `<-` arrow notation in Parameter Classification.

17. If any validation fails -> fix the issue and re-validate (max 3 iterations). If unable to fix -> document the issue in the completion report.

## Rules

### General
- File paths in SKILL.md use relative paths from project root (e.g., `infra/cfn/{service}/{service}.yml`).
- When updating existing files, preserve content that is not being changed. Do not rewrite unchanged sections.

### Stack Rules
- Namespace and Environment parameters are mandatory in every CFN template with the exact AllowedPattern from REFERENCE.md Section 4. No exceptions.
- All CFN outputs must use `Export: Name: !Sub '${AWS::StackName}-{OutputKey}'`.
- SKILL.md frontmatter `name` is kebab-case: `ipa-stack-{service}`.
- Stack name suffix defaults to the service name unless the user specifies otherwise.
- Never create IAM resources without setting Capabilities to `CAPABILITY_NAMED_IAM`.
- Every Known Deferral must have a Reason and Risk assessment.
- The CFN template directory name and the SKILL.md template path must be consistent: `infra/cfn/{service}/{service}.yml`.

## Completion Report

**Created/Updated:**
- Template: `infra/cfn/{service}/{service}.yml`
- Skill: `.claude/skills/ipa.stack.{service}/SKILL.md`
- Security: `.claude/skills/ipa.stack.{service}/SECURITY.md`
- Troubleshoot: `.claude/skills/ipa.stack.{service}/TROUBLESHOOT.md`

**Stack Summary**:
- Parameters: {count} ({config} configuration, {wirable_req} wirable-required, {wirable_opt} wirable-optional)
- Outputs: {count} exported
- Capabilities: {none or CAPABILITY_NAMED_IAM}

**Next steps:**
- Validate template: `aws cloudformation validate-template --template-body file://infra/cfn/{service}/{service}.yml`
- Compose: `/ipa-compose`
- Deploy: `/ipa-deploy`
