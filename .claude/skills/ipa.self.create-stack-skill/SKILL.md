---
name: ipa-self-create-stack-skill
description: "Create or update an IPA stack skill with its CloudFormation template and supporting files (SKILL.md, SECURITY.md, TROUBLESHOOT.md). Use when the user says 'create a stack skill', 'new stack skill', 'add a stack for [service]', 'write a stack skill', 'update the [service] stack skill', 'add [service] to IPA', or wants to add a new AWS infrastructure component to the IPA pattern system. Do NOT use for pattern composition (that is ipa.compose) or for deploying existing stacks (that is ipa.deploy)."
---

# ipa.self.create-stack-skill

Create or update an IPA stack skill — the complete set of SKILL.md, SECURITY.md, TROUBLESHOOT.md, and CloudFormation template — following established conventions so the output is compatible with `ipa.compose`.

## User Input

```text
$ARGUMENTS
```

Expected: `[create|update] [service-name]` — e.g., `create sqs`, `update lambda`.
If mode is omitted, infer from whether `.claude/skills/ipa.stack.{service}/SKILL.md` exists.
If service-name is omitted, ask the user.

## Pre-Execution Checks

1. Read [REFERENCE.md](REFERENCE.md) for structural contracts and conventions. Keep it in context throughout — all sections are needed during authoring.
2. Determine mode:
   - If `.claude/skills/ipa.stack.{service}/SKILL.md` exists -> **update** mode.
   - If it does not exist -> **create** mode.
   - If the user explicitly specified a mode that conflicts with file state -> ask: "Stack skill already exists. Switch to update mode?" (or vice versa).
3. If mode is **update**: read all existing files in `.claude/skills/ipa.stack.{service}/` and `infra/cfn/{service}/`. Note which files exist and which are absent — absent files will be created as part of the update.
4. If mode is **create**: verify the service name does not collide with an existing stack suffix. Check the Existing Stack Inventory table in REFERENCE.md.

## Execution Steps

### Phase 1: Gather Requirements

5. Collect the following from the user, one question at a time. For **update** mode, pre-populate answers from existing files and ask only about changes.

   a. **AWS service and purpose** — "What AWS service does this stack deploy, and what is its role in the architecture?"
      Example answer: "SQS queue for async message processing between API and workers"

   b. **Key resources** — "What CloudFormation resource types will the template create?"
      Example answer: "AWS::SQS::Queue, AWS::SQS::QueuePolicy"

   c. **Parameters** — For each parameter beyond Namespace and Environment, collect:
      - Name, Type, Default value, Validation pattern or allowed values, Error message
      - Classification: Configuration, Wirable — Required, Wirable — Optional, or Pattern-provided (see REFERENCE.md Section 5)
      - For Wirable parameters: which upstream stack and output provides the value

   d. **Outputs** — For each output, collect:
      - Name, Description
      - Used By: which downstream stacks or operational steps consume it

   e. **Capabilities** — Does the template create IAM resources (roles, policies)?
      - If yes -> `CAPABILITY_NAMED_IAM`
      - If no -> `none`

   f. **Stack name suffix** — What suffix for `{APP_NAMESPACE}-{APP_ENV}-{suffix}`?
      Default: the service name (e.g., `sqs`). Multi-instance stacks use variable suffixes (e.g., `queue-{name}`).

   g. **Multi-instance support** — Can this stack be deployed multiple times with different suffixes?

   h. **Build requirements** — Does this stack need a pre-built artifact (container image, frontend bundle)?
      If yes: Type, Suffix, Dockerfile/build path, Description.

   i. **Security posture** — Collect:
      - Deployment IAM actions (what the Builder Role needs)
      - Runtime permissions (what the deployed resource grants, if any)
      - Security controls enforced by the template
      - Known deferrals for POC scope

6. If mode is **update**: present a summary of what will change across all files and confirm before proceeding.

### Phase 2: Create CloudFormation Template

7. Create directory `infra/cfn/{service}/` if it does not exist.

8. Write `infra/cfn/{service}/{service}.yml` following the CloudFormation Template Skeleton in REFERENCE.md Section 4:
   - Namespace and Environment parameters with the standard AllowedPattern (copy exactly from REFERENCE.md).
   - Service-specific parameters with appropriate AllowedPattern, AllowedValues, and ConstraintDescription.
   - Conditions section if any Wirable — Optional parameters exist.
   - Resources with `!Sub` for dynamic naming using `${Namespace}` and `${Environment}`.
   - Tags on every taggable resource (at minimum: `Environment`).
   - Outputs exported via `Export: Name: !Sub '${AWS::StackName}-{OutputKey}'`.

9. Validate the template:
   ```
   aws cloudformation validate-template --template-body file://infra/cfn/{service}/{service}.yml
   ```
   - If validation succeeds -> proceed to Phase 3.
   - If validation fails -> fix the template and re-validate (max 3 iterations).
   - If still failing after 3 iterations -> stop and report the validation error to the user.

### Phase 3: Create Skill Files

10. Create directory `.claude/skills/ipa.stack.{service}/` if it does not exist.

11. Write `.claude/skills/ipa.stack.{service}/SKILL.md` following REFERENCE.md Section 1. Every section is mandatory except Build Requirements and Naming Convention (include only when applicable):
    - Frontmatter: `name: ipa-stack-{service}`, `description: "{one sentence}"`
    - H1 title and summary paragraph
    - CloudFormation Contract (Template, Stack name, Capabilities)
    - Parameters table (Namespace and Environment first, with exact validation from REFERENCE.md)
    - Parameter Classification subsection (categorize every parameter)
    - Outputs table (every output with Export Convention and Used By)
    - Build Requirements (only if applicable)
    - Naming Convention (only if physical naming differs from stack naming)
    - Security Summary with links to SECURITY.md

12. Write `.claude/skills/ipa.stack.{service}/SECURITY.md` following REFERENCE.md Section 2:
    - Deployment Permissions — YAML code block with actions, resource ARN, purpose
    - Runtime Permissions — YAML code block (only if the resource grants runtime permissions)
    - Security Controls — YAML code block with type, enabled, method
    - Known Deferrals — table with Deferral, Reason, Risk columns

13. Write `.claude/skills/ipa.stack.{service}/TROUBLESHOOT.md` following REFERENCE.md Section 3:
    - Failure Catalog table — minimum three rows: creation failure, deletion failure, no-updates
    - Additional Troubleshooting subsections for service-specific issues

### Phase 4: Validate

**ultrathink** — Shallow validation here means the skill ships with wiring incompatibilities that only surface when `ipa.compose` tries to consume it, or with inconsistencies between the CFN template and skill files that cause deploy-time failures.

14. Cross-validate consistency across all four files:
    - Every parameter in SKILL.md Parameters table exists in the CFN template with matching name, type, and validation.
    - Every output in SKILL.md Outputs table exists in the CFN template with matching export name.
    - Every IAM action in SECURITY.md Deployment Permissions corresponds to a resource type in the CFN template.
    - Parameter Classification in SKILL.md matches the actual parameter sources (Configuration params have defaults or .env sources; Wirable params reference real upstream stacks and outputs).
    - Output "Used By" entries reference known stacks or reasonable operational steps.
    - If the template uses `CAPABILITY_NAMED_IAM`, the CloudFormation Contract says so (and vice versa).

15. Verify `ipa.compose` compatibility (see REFERENCE.md Section 8):
    - SKILL.md has all four required sections with exact heading names: `## CloudFormation Contract`, `## Parameters`, `### Parameter Classification`, `## Outputs`.
    - Parameter table columns are: Parameter, Type, Default, Validation, Error Message.
    - Output table columns are: Output, Description, Export Convention, Used By.
    - Wirable parameters use the `<-` arrow notation in Parameter Classification.
    - Output Export Convention follows `{StackName}-{OutputKey}` pattern.
    - Stack name follows `{APP_NAMESPACE}-{APP_ENV}-{suffix}` convention.

16. If any validation fails -> fix the issue in the affected file(s) and re-validate (max 3 iterations). If unable to fix after 3 iterations -> document the remaining issue in the completion report and warn the user.

## Rules

- Namespace and Environment parameters are mandatory in every CFN template with the exact AllowedPattern from REFERENCE.md Section 4. No exceptions.
- All CFN outputs must use `Export: Name: !Sub '${AWS::StackName}-{OutputKey}'`.
- SKILL.md frontmatter `name` is kebab-case: `ipa-stack-{service}`.
- SKILL.md frontmatter `description` is a single sentence summarizing the deployment.
- Stack name suffix defaults to the service name unless the user specifies otherwise.
- Never create IAM resources in a template without setting Capabilities to `CAPABILITY_NAMED_IAM` in the CloudFormation Contract.
- Every Known Deferral must have a Reason and Risk assessment.
- File paths in SKILL.md use relative paths from project root (e.g., `infra/cfn/{service}/{service}.yml`).
- When updating an existing stack skill, preserve any content that is not being changed. Do not rewrite unchanged sections.
- The CFN template directory name and the SKILL.md template path must be consistent: `infra/cfn/{service}/{service}.yml`.

## Completion Report

**Created/Updated:**
- Template: `infra/cfn/{service}/{service}.yml`
- Skill: `.claude/skills/ipa.stack.{service}/SKILL.md`
- Security: `.claude/skills/ipa.stack.{service}/SECURITY.md`
- Troubleshoot: `.claude/skills/ipa.stack.{service}/TROUBLESHOOT.md`

**Summary:**
- Parameters: {count} ({config} configuration, {wirable_req} wirable-required, {wirable_opt} wirable-optional)
- Outputs: {count} exported
- Capabilities: {none or CAPABILITY_NAMED_IAM}
- Mode: {create or update}

**Next steps:**
- Validate template: `aws cloudformation validate-template --template-body file://infra/cfn/{service}/{service}.yml`
- Add to a pattern: edit `.claude/skills/ipa.compose/patterns/{pattern}/PATTERN.md`
- Compose with existing stacks: `/ipa.compose`
- Test deployment: `/ipa.deploy`
