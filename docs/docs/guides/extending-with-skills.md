---
title: Extending with Skills
sidebar_position: 6
---

# Extending with Skills

## Overview

This guide walks through creating a custom IPA stack skill using `/ipa-author-stack`. By the end, the reader has authored a new stack skill with a CloudFormation template, SKILL.md, SECURITY.md, and TROUBLESHOOT.md that integrates with `/ipa-compose` and the Makefile generation pipeline.

## When to Use This Guide

Use this guide when:

- An engagement requires an AWS service not covered by the built-in stacks (e.g., RDS, ElastiCache, Step Functions, SES)
- A custom tier stack is needed that bundles multiple related services into a single deployable unit with feature flags
- An existing CloudFormation template needs to be wrapped as a composable stack skill for use with `/ipa-compose`
- The stack library needs to be extended with a reusable stack skill for use across multiple engagements

Do not use this guide to compose or deploy existing stacks — see [Composing a Solution](composing-solution.md) instead.

## Before You Start

Before starting, confirm the following:

- `.env` file exists with `APP_NAMESPACE`, `APP_ENV`, `AWS_REGION`, `AWS_ACCOUNT_ID`, and `AWS_PROFILE` set
- An initialized project with at least one successful `/ipa-compose` run (confirms the skill infrastructure is working)
- A CloudFormation template or design document for the new stack, including the AWS resources to create, parameters, and outputs
- Familiarity with CloudFormation template authoring (parameters, resources, outputs, exports)
- Understanding of the IPA skill directory layout: each stack skill lives at `.claude/skills/ipa-stack-NAME/` with SKILL.md, SECURITY.md, and TROUBLESHOOT.md

Reference files for structural conventions:

- `.claude/skills/ipa-author-stack/REFERENCE.md` — authoritative reference for all stack skill and pattern contracts
- `.claude/skills/ipa-stack-ecr/` — simple prepare stack example (single service, no wirable parameters)
- `.claude/skills/ipa-stack-backend/` — tier stack example (multiple services, feature flags, wirable parameters)

## Before / Target State

| Before | After |
|--------|-------|
| A CloudFormation template or design for infrastructure not part of the built-in stacks | CloudFormation template at `infra/cfn/NAME/NAME.yml` following IPA conventions |
| No stack skill — the infrastructure cannot be selected or wired by `/ipa-compose` | Complete stack skill at `.claude/skills/ipa-stack-NAME/` with SKILL.md, SECURITY.md, and TROUBLESHOOT.md |
| No compose integration | The new stack appears as a selectable option in `/ipa-compose` with auto-wiring support |

## Steps

### 1. Design the stack interface

Before invoking the authoring skill, plan the stack interface. Define the following for each item:

**Parameters:**
- Which parameters beyond Namespace and Environment does the stack need?
- For each parameter, determine its classification:
  - **Configuration** — sourced from `.env` or template defaults (e.g., `MemorySize`, `Timeout`)
  - **Wirable — Required** — must be populated from an upstream stack output (e.g., `ImageUri` from ECR)
  - **Wirable — Optional** — defaults to empty string, conditionally enables resources (e.g., `SqsQueueUrl`)

**Outputs:**
- What values do downstream stacks or operational steps need?
- Every output must be exported using the convention `{StackName}-{OutputKey}`

**Lifecycle:**
- **prepare** — one-time prerequisites that survive teardown (e.g., ECR, Cognito)
- **deploy** — application stacks created and destroyed together

**Wiring:**
- Which existing stacks provide inputs to this stack?
- Which downstream stacks consume this stack's outputs?

### 2. Run /ipa-author-stack

To scaffold the stack skill, invoke the authoring skill:

```
/ipa-author-stack create NAME
```

Replace `NAME` with the service name (lowercase, e.g., `rds`, `elasticache`, `stepfn`).

The skill detects the authoring mode based on the input:

| Input | Mode |
|-------|------|
| Names a single AWS service (e.g., `rds`, `ses`) | Single-service prepare stack |
| Describes a multi-service scenario or names a tier concept | Combined (tier stack + pattern definition) |
| Target files already exist | Update mode |

The skill walks through an interactive requirements gathering phase, collecting architecture overview, parameters, outputs, capabilities, security posture, and lifecycle classification. It then generates four artifacts:

- `infra/cfn/NAME/NAME.yml` — CloudFormation template
- `.claude/skills/ipa-stack-NAME/SKILL.md` — stack skill metadata
- `.claude/skills/ipa-stack-NAME/SECURITY.md` — security advisory
- `.claude/skills/ipa-stack-NAME/TROUBLESHOOT.md` — failure catalog

### 3. Review the CloudFormation template

After the skill generates the template, review `infra/cfn/NAME/NAME.yml` for correctness. Confirm these IPA conventions are followed:

**Mandatory parameters** — Namespace and Environment are the first two parameters with the exact validation pattern:

```yaml
Parameters:
  Namespace:
    Type: String
    AllowedPattern: '^[a-z][a-z0-9-]{0,11}$'
    ConstraintDescription: 'Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter'
  Environment:
    Type: String
    AllowedPattern: '^[a-z][a-z0-9-]{0,11}$'
    ConstraintDescription: 'Must be 1-12 chars, lowercase letters/digits/hyphens, starts with letter'
```

**Resource naming** — all resources use `!Sub '${Namespace}-${Environment}-suffix'` with no hardcoded account IDs or regions.

**Output exports** — every output uses the standard export convention:

```yaml
Outputs:
  ExampleOutput:
    Description: 'Description of the output'
    Value: !GetAtt Resource.Attribute
    Export:
      Name: !Sub '${AWS::StackName}-ExampleOutput'
```

**Conditions** — wirable-optional parameters use conditions to gate resources:

```yaml
Conditions:
  HasOptionalParam: !Not [!Equals [!Ref OptionalParam, '']]
```

To validate the template syntax, run:

```bash
aws cloudformation validate-template \
  --template-body file://infra/cfn/NAME/NAME.yml
```

A successful validation returns the template description and parameter list. Fix any errors and re-validate before proceeding.

### 4. Verify SKILL.md compose compatibility

Open `.claude/skills/ipa-stack-NAME/SKILL.md` and confirm it contains the four sections that `/ipa-compose` requires, with exact heading names:

| Section | Heading | Purpose |
|---------|---------|---------|
| CloudFormation Contract | `## CloudFormation Contract` | Template path, stack name suffix, capabilities |
| Parameters | `## Parameters` | Parameter table with columns: Parameter, Type, Default, Validation, Error Message |
| Parameter Classification | `### Parameter Classification` | Classification under Parameters, using `<-` arrow notation for wirable parameters |
| Outputs | `## Outputs` | Output table with columns: Output, Description, Export Convention, Used By |

The Parameter Classification section is critical for auto-wiring. Wirable parameters must use the arrow notation so `/ipa-compose` can resolve connections:

```markdown
**Wirable — Required** (1) — sourced from upstream stack outputs:
- ImageUri <- ipa-stack-ecr `RepositoryUri`
```

:::warning
If any of the four required sections are missing or use different heading names, `/ipa-compose` validation (V3) rejects the stack skill. The heading names must match exactly.
:::

### 5. Review the SECURITY.md

Open `.claude/skills/ipa-stack-NAME/SECURITY.md` and confirm it documents:

- **Deployment Permissions** — IAM actions the Builder Execution Role needs, scoped to the tightest resource ARN possible
- **Security Controls** — hardcoded security posture (encryption, access control, logging)
- **Known Deferrals** — any security items deferred for POC scope, each with a Reason and Risk assessment

If the new stack requires IAM actions not covered by the current Builder Execution Role, update the role's policy or re-run `/ipa-security` to switch configuration paths.

### 6. Test composition

To verify the new stack integrates with the composition pipeline, run:

```
/ipa-compose
```

Select the new stack when prompted. The compose skill reads the SKILL.md, validates the sections, resolves wiring, and generates Makefiles.

After composition completes, verify the generated artifacts in `scripts/`:

- `scripts/deploy.mk` (or `scripts/prepare.mk` for prepare-lifecycle stacks) contains a `deploy-NAME` target with the correct `--template-file`, `--parameter-overrides`, and `--capabilities`
- Wiring is resolved: `$(eval)` lines fetch outputs from upstream stacks and pass them as parameter overrides
- `scripts/SECURITY-DISPOSITION.md` includes any Known Deferrals from the new stack

### 7. Deploy and verify

To deploy the new stack, run:

```
/ipa-deploy
```

After deployment completes, confirm the stack was created:

```bash
aws cloudformation describe-stacks \
  --stack-name $(APP_NAMESPACE)-$(APP_ENV)-NAME \
  --query 'Stacks[0].StackStatus' \
  --output text
```

The expected output is `CREATE_COMPLETE`.

To confirm outputs are accessible to downstream stacks, list the stack exports:

```bash
aws cloudformation describe-stacks \
  --stack-name $(APP_NAMESPACE)-$(APP_ENV)-NAME \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table
```

The output table lists each exported key and its value.

## Verification

To verify the full workflow succeeded, confirm these checks:

1. `/ipa-compose` lists the new stack as a selectable option and composes without validation errors.

2. Generated Makefiles include targets for the new stack. To check:

   ```bash
   grep 'deploy-NAME' scripts/deploy.mk
   ```

   This returns the deploy target line for the new stack.

3. The CloudFormation stack is deployed and healthy:

   ```bash
   aws cloudformation describe-stacks \
     --stack-name $(APP_NAMESPACE)-$(APP_ENV)-NAME \
     --query 'Stacks[0].StackStatus' \
     --output text
   ```

   Expected: `CREATE_COMPLETE`

4. Stack outputs are exported and accessible via CloudFormation exports:

   ```bash
   aws cloudformation list-exports \
     --query "Exports[?starts_with(Name, '$(APP_NAMESPACE)-$(APP_ENV)-NAME')].[Name,Value]" \
     --output table
   ```

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `aws cloudformation validate-template` fails with `Template format error` | Namespace or Environment parameter missing the required `AllowedPattern`, or YAML syntax error in the template | Add the exact `AllowedPattern` from REFERENCE.md Section 4 to both parameters. Run a YAML linter to check syntax. |
| `/ipa-compose` validation fails with "missing required section" | SKILL.md is missing one of the four required sections (`## CloudFormation Contract`, `## Parameters`, `### Parameter Classification`, `## Outputs`) or uses a different heading name | Add the missing section with the exact heading name. See REFERENCE.md Section 8 for the required section list. |
| Wiring resolution fails — parameter marked as "unresolved" | The `<-` arrow notation in Parameter Classification is missing, malformed, or references a stack not in the composition | Add or correct the arrow notation: `ParamName <- ipa-stack-source \`OutputKey\``. Confirm the source stack is included in the pattern. |
| `CREATE_FAILED` during deployment with parameter validation error | A required parameter is missing from `--parameter-overrides` in the generated Makefile, or a parameter value does not match the `AllowedPattern` | Check the Makefile target for the missing parameter. Verify the parameter value format against the `AllowedPattern` in the CloudFormation template. Re-compose with `/ipa-compose` to regenerate. |

## Next Steps

- **Compose the new stack into a solution** — see [Composing a Solution](composing-solution.md)
- **Stack skills reference** — see [Stack Skills](/developer-docs/skills/stack-skills) for documentation on all built-in stack skills
- **Author skills reference** — see [Author Skills](/developer-docs/skills/author-skills) for documentation on `/ipa-author-stack`
- **Update security permissions** — run `/ipa-security` if the new stack requires IAM actions not covered by the current role
- **Tear down the deployment** — run `/ipa-destroy` (see [Path to Production](path-to-production.md) for lifecycle management)
