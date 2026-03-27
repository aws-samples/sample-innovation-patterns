# Resource Skill Design and Implementation Guidance

Resource skills define the infrastructure that the Innovation Patterns Agent (IPA) deploys. They are the nouns of the system — CloudFormation stacks, deployable patterns, security metadata — consumed by process skills that orchestrate the deployment workflow [1]. Because resource skills translate directly into AWS infrastructure, any imprecision in their design produces failures that are difficult to diagnose and expensive to reverse.

This document provides the structural specification, templates, and quality standards for authoring resource skills. It is intended to be consumed by both human skill authors and AI agents that compose resource skills into deployable solutions.

## 1. Non-Negotiable Rules

The following rules apply to every resource skill without exception. They are deliberate design choices that constrain the authoring process to the one safe path [2][3].

1. **Never modify a bundled CloudFormation template at runtime.** Templates are authored once and versioned with the skill. The agent reads and deploys them; it does not edit them. Runtime modification introduces drift between the template on disk and the deployed infrastructure [4].

2. **Declare every parameter with a validation pattern.** Every CloudFormation parameter the stack accepts must have a corresponding regex pattern, error message, and recovery action in the SKILL.md parameter table. No freeform parameters [5].

3. **Declare every IAM action explicitly in the security advisory.** The security advisory must list exact IAM action names (e.g., `dynamodb:PutItem`), not wildcards (`dynamodb:*`) and not prose descriptions ("appropriate permissions"). The `/ipa.security` skill composes least-privilege policies from these declarations [1][7].

4. **Use the naming convention without exception.** Stack names follow `{APP_NAMESPACE}-{APP_ENV}-{service_suffix}`. Resource names follow `{APP_NAMESPACE}-{APP_ENV}-{resource_type}` or `{APP_NAMESPACE}_{APP_ENV}_{resource_type}` for services that prohibit hyphens. Deviation breaks cross-stack references, security policies, and the eject workflow [1][4][5][7].

5. **Stop immediately on any deployment error.** If a CloudFormation operation returns an error, the agent must not continue to the next step. Every resource skill must include the directive: "STOP immediately if any deployment step fails. Do not continue to the next step." [4]

6. **Declare inter-stack wiring explicitly.** Pattern skills must specify every output-to-input connection in a structured wiring map. The agent must never improvise wiring — never pass an output from a stack other than the declared source, never invent parameter values [1][4].

7. **Ensure idempotency.** Running a resource skill against existing infrastructure must not destroy or corrupt that infrastructure. CloudFormation's `deploy` command is inherently idempotent (it creates or updates). A "No updates are to be performed" response is a success, not an error [1][5].

8. **Never include real credentials, account IDs, or endpoints in examples or templates.** All examples must use parameter references or placeholder values [3].

### 1.1 Why These Rules Exist

Resource skills occupy the lowest-freedom position in the IPA skill library. The Anthropic Skill Authoring Best Practices describe this as the "narrow bridge with cliffs on both sides" — there is one safe way forward, and deviation causes real failures [2]. Infrastructure commands that deploy CloudFormation stacks, create IAM roles, or provision S3 buckets produce side effects that persist in the AWS account. A misrouted output, a misspelled stack name, or an overly broad IAM policy does not fail visibly at composition time; it fails at runtime, often in a different stack, producing error messages that do not point back to the root cause.

These rules exist to make the literal, mechanical path through a resource skill the correct one. The skill author's responsibility is to eliminate every opportunity for the agent to improvise [2][4].

## 2. Resource Skill Taxonomy

The IPA framework organizes resource skills into two tiers, each with a distinct purpose and authoring pattern [1].

A **stack skill** (`/ipa.stack.*`) is the atomic unit. It wraps a single primary AWS service — such as DynamoDB, Lambda, Cognito, or S3 — with its CloudFormation template, parameters, expected outputs, and security metadata. A stack skill is self-contained: it does not reference other stacks. It declares what it provisions and what permissions it requires, but it does not know which pattern will consume it [1][7].

A **pattern skill** (`/ipa.pattern.*`) is the composition unit. It composes multiple stack skills into a deployable solution — a full-stack application. A pattern skill defines the deployment order of its constituent stacks, the parameter wiring between them, and the inter-stack dependencies. It does not own CloudFormation templates; it references stack skills that do [1][4].

| Concern | Stack Skill | Pattern Skill |
|---------|------------|---------------|
| Primary content | CloudFormation template + metadata | Stack sequence + wiring map |
| Security role | Declares required permissions | Consumed by `/ipa.security` to compose policies |
| Parameters | Service-specific (table name, bucket name) | Wiring-specific (which output feeds which input) |
| Outputs | ARNs, URLs, IDs for dependent stacks | Aggregated outputs for runbook and Makefiles |
| Deployment unit | One CloudFormation stack | Ordered sequence of stack deployments |
| Degrees of freedom | Very low | Low |

Determine which type of resource skill is required before proceeding. Sections 3 and 4 provide separate specifications for each type.

## 3. Stack Skill Specification

A stack skill is the foundational building block of the IPA resource library. Each stack skill encapsulates one AWS service with everything the IPA framework needs to deploy it, secure it, compose it into patterns, and document it in a runbook [1][7].

### 3.1 Directory Structure

Every stack skill resides in its own directory under `.claude/skills/`. All reference files are one level deep from SKILL.md — no nested references [2].

```text
ipa.stack.{service}/
  SKILL.md              # Metadata, parameters, outputs, security summary (~150 lines)
  template.yml          # CloudFormation template (read by /ipa.deploy, never modified)
  SECURITY.md           # Detailed security advisory (read by /ipa.security)
  TROUBLESHOOT.md       # Failure catalog with detection and recovery procedures
```

The SKILL.md file is loaded into the agent's context when the skill is triggered. The remaining files are read on demand: `template.yml` during deployment, `SECURITY.md` during security composition, and `TROUBLESHOOT.md` when an error occurs [2][6].

### 3.2 SKILL.md Template

The following template contains every required section for a stack skill's SKILL.md file. Copy it and replace the bracketed placeholders with service-specific content.

````markdown
---
name: ipa-stack-{service}
description: "Deploy a {Service Name} stack with {primary capability}. Use when the
  user invokes /ipa.stack.{service} or when /ipa.compose references this stack."
---

# {Service Name} Stack

## CloudFormation Contract

- **Template**: [template.yml](template.yml)
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-{service_suffix}`
- **Capabilities**: `{CAPABILITY_NAMED_IAM | CAPABILITY_AUTO_EXPAND | none}`

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace" |
| Environment | String | — | `dev \| staging \| prod` | "Must be dev, staging, or prod" |
| {Param1} | {Type} | {default or —} | {regex or enum} | "{specific error}" |
| {Param2} | {Type} | {default or —} | {regex or enum} | "{specific error}" |

Every parameter in this table must have a corresponding `Parameter` entry in template.yml.

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| {Output1} | {what it provides} | `{APP_NAMESPACE}-{APP_ENV}-{service_suffix}-{output}` | {consuming stack(s)} |
| {Output2} | {what it provides} | `{APP_NAMESPACE}-{APP_ENV}-{service_suffix}-{output}` | {consuming stack(s)} |

Output names are stable across versions. Renaming an output is a breaking change.

## Security Summary

**Required IAM actions**: {Category-level summary, e.g., "DynamoDB read/write on TableArn"}
**Security controls**: {e.g., "Encryption at rest (SSE), public access blocked"}
**Full advisory**: See [SECURITY.md](SECURITY.md)

## Dependencies

- **Requires**: {list of .env variables or stack outputs this stack needs, or "None"}
- **Provides**: {list of outputs other stacks consume}
````

**Frontmatter rules** (per Anthropic guidance [2]):
- `name`: maximum 64 characters, lowercase letters, numbers, and hyphens only
- `description`: maximum 1024 characters, third person, includes both what the skill does and when to use it

### 3.3 CloudFormation Template Requirements

The `template.yml` file is the source of truth for the infrastructure this stack provisions. It is authored once, versioned alongside the skill, and deployed without modification [4][5][7].

**Required structural elements:**

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: "{Service Name} stack for IPA — {one-line purpose}"

Parameters:
  Namespace:
    Type: String
    AllowedPattern: "^[a-z][a-z0-9-]{0,11}$"
  Environment:
    Type: String
    AllowedValues:
      - dev
      - staging
      - prod
  # Service-specific parameters follow

Resources:
  # Service resources

Outputs:
  # Every output declared in SKILL.md must appear here
```

**Template rules:**

1. Every parameter in the SKILL.md parameter table must have a corresponding `Parameters` entry with `AllowedPattern` or `AllowedValues` as a second line of defense.
2. Every output in the SKILL.md output table must have a corresponding `Outputs` entry.
3. No hardcoded account IDs, regions, or environment-specific values. All environment-specific values come through parameters or pseudo-parameters (`AWS::AccountId`, `AWS::Region`).
4. Resource names must follow the naming convention: `!Sub "${Namespace}-${Environment}-{resource_type}"`.
5. The agent must never edit this file. If the template needs changes, the skill author updates and versions it.

### 3.4 Parameter Validation Table

Every parameter the stack accepts must have a validation entry. This table serves as the contract between the skill author (who knows what values are valid) and the process skills (which supply values at deployment time) [5].

**Template:**

| Parameter | Type | Default | Validation Pattern | Error Message | Recovery Action |
|-----------|------|---------|--------------------|---------------|-----------------|
| Namespace | String | — (required) | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — must be 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" | "Run /ipa.init to set APP_NAMESPACE" |
| Environment | String | — (required) | `dev \| staging \| prod` | "Invalid environment — must be one of: dev, staging, prod" | "Run /ipa.init to set APP_ENV" |
| TableName | String | — (required) | `/^[a-zA-Z0-9._-]{3,255}$/` | "Invalid table name — 3-255 chars, alphanumeric, dots, underscores, hyphens" | "Check APP_NAMESPACE and APP_ENV values" |

**Rules:**

- Every parameter has a row. No exceptions.
- Validation patterns use regex where applicable and enum membership for constrained values.
- Error messages are specific — they name the invalid field, state the constraint, and show the expected format.
- Recovery actions tell the operator (human or agent) how to fix the problem, not just that it is wrong.

### 3.5 Output Declaration

Outputs are the mechanism by which stacks communicate within a pattern. Each output declared in SKILL.md becomes available for wiring in pattern skills [1][7].

**Template:**

| Output Name | Description | Export Convention | Used By |
|-------------|-------------|-------------------|---------|
| TableArn | ARN of the provisioned DynamoDB table | `{Namespace}-{Environment}-ddb-TableArn` | ipa.stack.lambda (dynamodb_table_arns) |
| TableName | Name of the provisioned DynamoDB table | `{Namespace}-{Environment}-ddb-TableName` | ipa.stack.lambda (env.TABLE_NAME) |

**Rules:**

- Output names must be PascalCase, stable across skill versions. Renaming an output is a breaking change — it invalidates every pattern skill that references it.
- The "Used By" column is advisory. It documents known consumers but does not restrict usage. New patterns may wire the output to different targets.
- Every output must have a corresponding `Outputs` entry in `template.yml` with a matching logical name.

### 3.6 Security Advisory Summary

The SKILL.md includes a brief security summary for quick reference. This summary is not consumed programmatically — it exists for human authors reviewing the skill and for agents that need a quick overview before reading the full advisory [1].

**Format:**

```markdown
## Security Summary

**Required IAM actions**: DynamoDB read/write (PutItem, GetItem, Query, Scan, DeleteItem) on TableArn
**Security controls**: Encryption at rest (AWS-managed SSE), point-in-time recovery enabled, no public access
**Full advisory**: See [SECURITY.md](SECURITY.md)
```

### 3.7 SECURITY.md Specification

The SECURITY.md file contains the detailed security advisory that `/ipa.security` reads to compose least-privilege IAM policies. This is the most critical metadata a stack skill provides — imprecise security metadata directly causes either permission errors (too restrictive) or overly broad policies (too permissive) [1][5][7].

**Template:**

```yaml
# Security Advisory: {Service Name} Stack

permissions:
  - actions:
      - dynamodb:PutItem
      - dynamodb:GetItem
      - dynamodb:Query
      - dynamodb:Scan
      - dynamodb:DeleteItem
      - dynamodb:UpdateItem
    resource: "!Output TableArn"
    purpose: "CRUD operations on the application table"

  - actions:
      - logs:CreateLogGroup
      - logs:CreateLogStream
      - logs:PutLogEvents
    resource: "arn:aws:logs:{AWS_REGION}:{AWS_ACCOUNT_ID}:log-group:/aws/lambda/*"
    purpose: "CloudWatch logging"

controls:
  - type: encryption_at_rest
    enabled: true
    method: "AWS-managed SSE (AES-256)"

  - type: public_access
    enabled: false
    enforcement: "No public-facing configuration; access restricted to VPC or IAM"

  - type: backup_recovery
    enabled: true
    method: "Point-in-time recovery enabled; 35-day retention"
```

**Field definitions:**

- `permissions[].actions`: Exact IAM action names. No wildcards. Each action must be individually necessary for the stack's intended function.
- `permissions[].resource`: The ARN pattern for the target resource. Use `!Output {OutputName}` to reference the stack's own outputs, which `/ipa.security` resolves to actual ARN values after deployment.
- `permissions[].purpose`: A one-line explanation of why these actions are required. This appears in the generated IAM policy as a comment and in the Deliverable Security Review matrix [1].
- `controls[]`: Security controls enforced by the CloudFormation template itself. These are not permissions — they are configurations (encryption, access blocking, backup) that the template provisions.

**Anti-pattern vs. correct pattern:**

```yaml
# WRONG: vague advisory
permissions:
  - actions: ["dynamodb:*"]
    resource: "*"
    purpose: "DynamoDB access"

# CORRECT: exact advisory
permissions:
  - actions:
      - dynamodb:PutItem
      - dynamodb:GetItem
      - dynamodb:Query
    resource: "!Output TableArn"
    purpose: "Read/write operations on the passengers table"
```

### 3.8 TROUBLESHOOT.md Specification

Every stack skill must include a failure catalog that maps symptoms to causes, detection methods, and exact recovery procedures [4][5]. The TROUBLESHOOT.md file is read by the agent when a deployment error occurs.

**Template:**

```markdown
# Troubleshooting: {Service Name} Stack

## ROLLBACK_COMPLETE

**Symptom**: Stack status is ROLLBACK_COMPLETE after deployment attempt.
**Cause**: Initial creation failed; CloudFormation rolled back all resources.
**Detection**:
  ```bash
  aws cloudformation describe-stacks \
    --stack-name {APP_NAMESPACE}-{APP_ENV}-{service_suffix} \
    --query 'Stacks[0].StackStatus' \
    --output text \
    --region {AWS_REGION} \
    --profile {AWS_PROFILE}
  ```
**Recovery**:
  1. Read the failure reason:
     ```bash
     aws cloudformation describe-stack-events \
       --stack-name {APP_NAMESPACE}-{APP_ENV}-{service_suffix} \
       --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
       --output table \
       --region {AWS_REGION} \
       --profile {AWS_PROFILE}
     ```
  2. Delete the failed stack:
     ```bash
     aws cloudformation delete-stack \
       --stack-name {APP_NAMESPACE}-{APP_ENV}-{service_suffix} \
       --region {AWS_REGION} \
       --profile {AWS_PROFILE}
     ```
  3. Wait for deletion:
     ```bash
     aws cloudformation wait stack-delete-complete \
       --stack-name {APP_NAMESPACE}-{APP_ENV}-{service_suffix} \
       --region {AWS_REGION} \
       --profile {AWS_PROFILE}
     ```
  4. Fix the root cause identified in step 1.
  5. Re-run the deployment.

## Permission Denied

**Symptom**: CREATE_FAILED with "User: arn:aws:iam::... is not authorized to perform: {action}".
**Cause**: The execution role lacks a required IAM permission.
**Detection**: Parse the error message for the denied action and target resource.
**Recovery**:
  1. Verify the SECURITY.md advisory includes the denied action.
  2. If missing: add the action to SECURITY.md and re-run `/ipa.security`.
  3. If present: the execution role was not updated. Re-run `/ipa.security` to recompose.

## Resource Already Exists

**Symptom**: CREATE_FAILED with "{ResourceType} already exists".
**Cause**: A resource with the same name exists outside this stack (created manually or by another stack).
**Detection**: Check if the resource name follows the naming convention.
**Recovery**:
  1. If the existing resource belongs to this project: import it or change the APP_NAMESPACE.
  2. If the existing resource is unrelated: change the APP_NAMESPACE via `/ipa.init`.
```

Every recovery procedure is an exact sequence of commands. No recovery step says "fix the issue" or "resolve the problem" — each one specifies what to run and what to check [2][4].

## 4. Pattern Skill Specification

A pattern skill composes multiple stack skills into a deployable solution. It defines which stacks to deploy, in what order, and how their outputs wire together. Pattern skills are where the highest composition risk exists — if the agent deviates from the declared wiring or reorders the deployment sequence, the resulting infrastructure may deploy but behave incorrectly [1][4].

### 4.1 Directory Structure

```text
ipa.pattern.{solution}/
  SKILL.md              # Stack sequence, wiring summary, prerequisites (~200 lines)
  WIRING.md             # Detailed output-to-input mapping (read by /ipa.compose)
  ARCHITECTURE.md       # Solution architecture for runbook generation
  TROUBLESHOOT.md       # Pattern-level failure catalog
```

A pattern skill directory does not contain a `template.yml` file. Pattern skills reference stack skills; they do not own CloudFormation templates [1].

### 4.2 SKILL.md Template

````markdown
---
name: ipa-pattern-{solution}
description: "Compose and deploy a {solution description}. Use when the user invokes
  /ipa.pattern.{solution} or when /ipa.compose selects this pattern."
---

# {Solution Name} Pattern

## Composition Type

{standalone | add-on to ipa.pattern.{base}}

## Prerequisites

- /ipa.init completed (.env exists with IPA project variables)
- /ipa.security completed (BUILDER_ROLE_ARN set in .env)
{- ipa.pattern.{base} deployed (add-on patterns only)}

## Stack Sequence

> **STOP immediately if any deployment step fails. Do not continue to the next step.**

1. Deploy **ipa.stack.dynamodb**. Depends on: none.
2. Deploy **ipa.stack.ecr**. Depends on: none. (Parallel with step 1.)
3. Deploy **ipa.stack.cognito**. Depends on: none. (Parallel with steps 1-2.)
4. Deploy **ipa.stack.lambda** (buffered). Depends on: ipa.stack.dynamodb outputs, ipa.stack.ecr outputs.
5. Deploy **ipa.stack.lambda** (streaming). Depends on: ipa.stack.dynamodb outputs, ipa.stack.ecr outputs.
6. Deploy **ipa.stack.apigw**. Depends on: ipa.stack.lambda outputs, ipa.stack.cognito outputs.
7. Deploy **ipa.stack.s3**. Depends on: none.
8. Deploy **ipa.stack.cloudfront**. Depends on: ipa.stack.s3 outputs, ipa.stack.apigw outputs.

## Wiring Summary

DynamoDB.TableArn → Lambda (buffered + streaming) dynamodb_table_arns
Cognito.UserPoolArn → API Gateway cognito_user_pool_arn
Cognito.IssuerUrl → Lambda (buffered + streaming) env.AUTH_ISSUER
Lambda.FunctionArn → API Gateway lambda_function_arn

**Full wiring map**: See [WIRING.md](WIRING.md)

## Environment Variable Contract

Every Lambda function in this pattern receives these environment variables:

| Variable | Source | Required |
|----------|--------|----------|
| APP_REGION | .env AWS_REGION | Yes |
| APP_ENV | .env APP_ENV | Yes |
| APP_NAMESPACE | .env APP_NAMESPACE | Yes |
| AUTH_ISSUER | ipa.stack.cognito → IssuerUrl | Yes |
| AUTH_AUDIENCE | ipa.stack.cognito → UserPoolClientId | Yes |
| {SERVICE_VAR} | {source} | {Yes/No} |

## Teardown Sequence

Reverse of deployment. Delete stacks in this order:

8. Delete ipa.stack.cloudfront
7. Delete ipa.stack.s3
6. Delete ipa.stack.apigw
5. Delete ipa.stack.lambda (streaming)
4. Delete ipa.stack.lambda (buffered)
3. Delete ipa.stack.cognito
2. Delete ipa.stack.ecr
1. Delete ipa.stack.dynamodb

Verify each stack reaches DELETE_COMPLETE before proceeding to the next.
````

### 4.3 WIRING.md Specification

The WIRING.md file is the single source of truth for inter-stack communication within a pattern. The `/ipa.compose` process skill reads this file to generate Makefiles and the runbook. The agent must never deviate from the declared wiring [1][4].

**Format:**

```yaml
# Wiring Map: {Solution Name}

wiring:
  # DynamoDB → Lambda
  - source:
      stack: ipa.stack.dynamodb
      output: TableArn
    target:
      stack: ipa.stack.lambda
      parameter: DynamoDbTableArns
    notes: "Grants Lambda read/write access to the table"

  - source:
      stack: ipa.stack.dynamodb
      output: TableName
    target:
      stack: ipa.stack.lambda
      env: TABLE_NAME
    notes: "Lambda uses this at runtime to construct table queries"

  # Cognito → API Gateway
  - source:
      stack: ipa.stack.cognito
      output: UserPoolArn
    target:
      stack: ipa.stack.apigw
      parameter: CognitoUserPoolArn
    notes: "API Gateway Cognito authorizer configuration"

  # Cognito → Lambda
  - source:
      stack: ipa.stack.cognito
      output: IssuerUrl
    target:
      stack: ipa.stack.lambda
      env: AUTH_ISSUER
    notes: "JWT validation at the application layer"

  - source:
      stack: ipa.stack.cognito
      output: UserPoolClientId
    target:
      stack: ipa.stack.lambda
      env: AUTH_AUDIENCE
    notes: "JWT audience claim verification"

  # Lambda → API Gateway
  - source:
      stack: ipa.stack.lambda
      output: FunctionArn
    target:
      stack: ipa.stack.apigw
      parameter: LambdaFunctionArn
    notes: "API Gateway Lambda proxy integration"

  # S3 + API Gateway → CloudFront
  - source:
      stack: ipa.stack.s3
      output: BucketDomainName
    target:
      stack: ipa.stack.cloudfront
      parameter: S3Origin
    notes: "Static asset origin"

  - source:
      stack: ipa.stack.apigw
      output: ApiUrl
    target:
      stack: ipa.stack.cloudfront
      parameter: ApiOrigin
    notes: "API origin for /api/* path routing"
```

**Field definitions:**

- `source.stack`: The stack skill that produces the output. Must match a stack in the Stack Sequence.
- `source.output`: The output name as declared in the source stack skill's Output table.
- `target.stack`: The stack skill that consumes the value.
- `target.parameter`: A CloudFormation parameter on the target stack. Use this when the value is consumed at deployment time.
- `target.env`: An environment variable on the target stack. Use this when the value is consumed at runtime (Lambda functions, ECS containers).
- `notes`: A one-line explanation of the connection's purpose. This appears in the generated runbook.

**Wiring validation rules:**

1. Every `source.output` must exist in the source stack skill's Output table. If it does not, the wiring is invalid.
2. Every `target.parameter` must exist in the target stack skill's Parameter table. If it does not, the wiring is invalid.
3. No circular dependencies: if stack A's output feeds stack B, then stack B's output must not feed stack A (directly or transitively).
4. Every required parameter on every stack in the sequence must be wired. A missing connection causes a deployment failure.

**Anti-pattern vs. correct pattern:**

```yaml
# WRONG: implicit wiring
wiring:
  - source: ipa.stack.cognito
    target: ipa.stack.apigw
    description: "Pass the relevant Cognito outputs to API Gateway"

# CORRECT: explicit wiring
wiring:
  - source:
      stack: ipa.stack.cognito
      output: UserPoolArn
    target:
      stack: ipa.stack.apigw
      parameter: CognitoUserPoolArn
```

### 4.4 ARCHITECTURE.md Specification

The ARCHITECTURE.md file is the one section of a resource skill where higher degrees of freedom are appropriate. It explains why these stacks compose together, what problem the pattern solves, and what the resulting architecture looks like [1][2].

This file serves a dual purpose: it provides context for agents composing the pattern, and it feeds the "Architecture Overview" section of the generated runbook — the document a customer's engineering team reads to understand the infrastructure they are inheriting [1].

**Required content:**

1. **Problem statement** — what use case does this pattern address? (1-2 paragraphs)
2. **Architecture diagram** — an ASCII or Mermaid diagram showing the stack dependency graph and data flow
3. **Stack-by-stack summary** — what each stack contributes to the solution (table or brief list)
4. **Alternatives considered** — why this composition was chosen over other approaches (optional but recommended)

**Example architecture diagram:**

```
                    ┌──────────────┐
                    │  CloudFront  │
                    └──────┬───────┘
                     /           \
            ┌───────┐         ┌──────────┐
            │  S3   │         │ API GW   │
            └───────┘         └────┬─────┘
                               /       \
                    ┌─────────┐     ┌──────────┐
                    │ Lambda  │     │ Lambda   │
                    │(buffer) │     │(stream)  │
                    └────┬────┘     └────┬─────┘
                         \              /
                      ┌──────────┐  ┌─────────┐
                      │ DynamoDB │  │ Cognito  │
                      └──────────┘  └─────────┘
```

### 4.5 Composition Types

The IPA framework supports two composition types for pattern skills [4]:

**Standalone patterns** deploy a complete solution from scratch. They have no infrastructure prerequisites beyond the IPA project configuration (`.env`) and security stack. Examples: `ipa.pattern.react-rest-lambda`, `ipa.pattern.sqs-lambda`.

**Add-on patterns** extend an existing deployed pattern. They assume specific stacks already exist and add or modify stacks to provide additional capability. Examples from the legacy implementation include a chat add-on that extends the react-rest-lambda pattern with conversational AI capability [4].

**Add-on pattern rules:**

1. The SKILL.md `Prerequisites` section must list the base pattern and the specific stacks that must exist.
2. The `Composition Type` field must state `add-on to ipa.pattern.{base}`.
3. The Stack Sequence must include verification steps that check for the existence of prerequisite stacks before deploying new ones:
   ```
   1. Verify ipa.stack.lambda exists in {APP_NAMESPACE}-{APP_ENV}-fn. STOP if not found.
   2. Deploy ipa.stack.sqs. Depends on: none.
   3. Update ipa.stack.lambda with SQS_QUEUE_URL environment variable.
   ```
4. Update steps (modifying existing stacks) must declare exactly what changes: which parameters are added, which environment variables are set, and which security permissions are needed.

### 4.6 Teardown Specification

Every pattern skill must include a teardown sequence that reverses the deployment safely. Teardown order is the reverse of deployment order — the last stack deployed is the first stack deleted [4].

**Rules:**

1. Each teardown step must verify the stack can be deleted. A stack that is referenced by another stack's CloudFormation import cannot be deleted until the dependent stack is deleted first.
2. Each step must wait for `DELETE_COMPLETE` before proceeding to the next deletion.
3. The teardown sequence must be presented as a numbered list in SKILL.md (see the template in Section 4.2).
4. Teardown must handle partial deployments — if only stacks 1-4 of an 8-stack pattern were deployed, the teardown sequence skips stacks 5-8.

## 5. Naming Convention Reference

The naming convention is a system invariant that spans every resource skill, every Makefile, every runbook, and every security policy in the IPA framework. Inconsistent naming breaks cross-stack references, prevents `/ipa.security` from composing correct IAM policies, and renders the eject workflow unreliable [1][4][5][7].

| Resource Type | Name Formula | Example | Notes |
|--------------|-------------|---------|-------|
| CloudFormation stack | `{APP_NAMESPACE}-{APP_ENV}-{service_suffix}` | `myapp-dev-ddb` | Service suffix is fixed per stack skill |
| DynamoDB table | `{APP_NAMESPACE}_{APP_ENV}_{table_name}` | `myapp_dev_passengers` | Underscores; hyphens not allowed in table names |
| S3 bucket | `{APP_NAMESPACE}-{APP_ENV}-{purpose}-{AWS_ACCOUNT_ID}-{AWS_REGION}` | `myapp-dev-logs-000000000000-us-east-1` | Account ID and region ensure global uniqueness |
| IAM role | `{APP_NAMESPACE}-{APP_ENV}-{role_type}` | `myapp-dev-builder` | Role types: `builder`, `codebuild`, `fn-exec` |
| Lambda function | `{APP_NAMESPACE}-{APP_ENV}-{function_type}` | `myapp-dev-fn` | Function types: `fn` (buffered), `fn-stream` |
| ECR repository | `{APP_NAMESPACE}-{APP_ENV}-{repo_type}` | `myapp-dev-ecr` | Lowercase only |
| CloudWatch log group | `/aws/{service}/{APP_NAMESPACE}-{APP_ENV}-{resource}` | `/aws/lambda/myapp-dev-fn` | Follows AWS convention |
| Environment variable | `APP_REGION`, `APP_ENV`, `APP_NAMESPACE` | — | Always present in Lambda; uppercase with underscores |

**Service suffix registry:**

| Stack Skill | Service Suffix |
|------------|---------------|
| ipa.stack.dynamodb | `ddb` |
| ipa.stack.lambda (buffered) | `fn` |
| ipa.stack.lambda (streaming) | `fn-stream` |
| ipa.stack.apigw | `apigw` |
| ipa.stack.s3 | `s3` |
| ipa.stack.cloudfront | `cf` |
| ipa.stack.cognito | `cognito` |
| ipa.stack.ecr | `ecr` |
| ipa.stack.sqs | `sqs` |
| ipa.stack.security | `security` |

When a new stack skill is created, the skill author must register a unique service suffix in this table before proceeding. Duplicate suffixes are not permitted.

## 6. Dual-Audience Design

Every resource skill serves two consumers: the AI agent that composes and deploys the infrastructure, and the runbook that a customer's engineering team reads to understand and maintain the infrastructure after the engagement ends [1].

The AI agent reads SKILL.md metadata — parameters, outputs, wiring maps, security advisories — to execute the deployment workflow. The runbook, generated by `/ipa.compose`, reads the same metadata to produce a human-readable, step-by-step deployment document. The CloudFormation template itself is the ultimate eject artifact: it is the infrastructure-as-code file that the customer's team will own, modify, and deploy through their own pipelines after the refactor step [1].

This dual-audience requirement has a direct implication for skill authors: metadata must be both machine-parseable (structured formats that scripts and agents can process reliably) and human-understandable (clear descriptions, meaningful names, documented purposes). The `notes` field in wiring maps, the `purpose` field in security advisories, and the `Description` field in output tables all exist to serve the runbook audience. Omitting these fields does not break the agent workflow, but it degrades the quality of the customer deliverable — and the quality of the customer deliverable is the measure of IPA's value on the path to production [1].

## 7. Quality Validation Checklist

The following checklist must pass before a resource skill is considered complete. This checklist can be used by human skill authors, by AI agents reviewing their own work, and by `/ipa.compose` as a pre-composition gate [2][5].

### Structure

- [ ] All required files are present (SKILL.md, template.yml or WIRING.md, SECURITY.md, TROUBLESHOOT.md)
- [ ] SKILL.md body is under 200 lines (stack skills) or 250 lines (pattern skills)
- [ ] All reference files are one level deep from SKILL.md
- [ ] No reference file exceeds 300 lines
- [ ] Frontmatter `name` follows the naming convention (`ipa-stack-{service}` or `ipa-pattern-{solution}`)
- [ ] Frontmatter `description` is under 1024 characters, third person, includes what and when

### Parameters

- [ ] Every CloudFormation parameter has a row in the SKILL.md parameter table
- [ ] Every parameter has a validation pattern (regex or enum)
- [ ] Every parameter has a specific error message
- [ ] Every parameter has a recovery action
- [ ] SKILL.md parameter table matches template.yml `Parameters` section exactly
- [ ] No parameter has a default that contains real credentials or account-specific values

### Outputs

- [ ] Every CloudFormation output has a row in the SKILL.md output table
- [ ] Every output has a description and export convention
- [ ] Output names are PascalCase
- [ ] SKILL.md output table matches template.yml `Outputs` section exactly

### Security

- [ ] SECURITY.md lists every IAM action required (no wildcards)
- [ ] Every permission entry has a `resource` field with a specific ARN pattern (no `"*"`)
- [ ] Every permission entry has a `purpose` field
- [ ] Security controls section documents encryption, access control, and backup settings
- [ ] No permission is broader than necessary for the stack's intended function

### Naming

- [ ] Stack name follows `{APP_NAMESPACE}-{APP_ENV}-{service_suffix}`
- [ ] Service suffix is registered in the naming convention reference
- [ ] Resource names within the template follow the naming convention
- [ ] No hardcoded names — all names are computed from parameters

### Idempotency

- [ ] Re-deploying the stack with unchanged parameters produces no errors
- [ ] "No updates are to be performed" is handled as success
- [ ] The template does not include resources that fail on re-creation (e.g., `AWS::S3::Bucket` with a fixed name requires `DeletionPolicy: Retain` or conditional creation)

### Wiring (Pattern Skills Only)

- [ ] Every source.output in WIRING.md exists in the source stack's output table
- [ ] Every target.parameter in WIRING.md exists in the target stack's parameter table
- [ ] No circular dependencies in the stack sequence
- [ ] Every required parameter on every stack is wired
- [ ] The error-first directive appears in the Stack Sequence section

### Eject

- [ ] Every output has a description suitable for runbook generation
- [ ] Every wiring entry has a `notes` field for the runbook
- [ ] The ARCHITECTURE.md file includes a diagram and stack-by-stack summary
- [ ] CloudFormation template includes `Description` on every resource (for inline documentation)

## 8. Anti-Patterns and Correct Patterns

AI agents pattern-match examples more reliably than they interpret abstract rules [2][6]. The following pairs demonstrate the most common and most dangerous authoring mistakes alongside their correct alternatives.

---

**1. Vague parameter description vs. validation table**

```yaml
# WRONG
## Parameters
The stack accepts a table name and region.
```

```yaml
# CORRECT
## Parameters
| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| TableName | String | — | `/^[a-zA-Z0-9._-]{3,255}$/` | "Invalid table name — 3-255 chars" |
| Region | String | — | `/^[a-z]{2}-[a-z]+-\d+$/` | "Invalid region — expected us-east-1 format" |
```

---

**2. Implicit output wiring vs. explicit wiring map**

```yaml
# WRONG
wiring:
  - source: ipa.stack.cognito
    target: ipa.stack.apigw
    description: "Pass the relevant Cognito outputs to API Gateway"
```

```yaml
# CORRECT
wiring:
  - source:
      stack: ipa.stack.cognito
      output: UserPoolArn
    target:
      stack: ipa.stack.apigw
      parameter: CognitoUserPoolArn
    notes: "Cognito authorizer configuration"
```

---

**3. Vague security advisory vs. exact IAM action list**

```yaml
# WRONG
permissions:
  - actions: ["dynamodb:*"]
    resource: "*"
    purpose: "Database access"
```

```yaml
# CORRECT
permissions:
  - actions:
      - dynamodb:PutItem
      - dynamodb:GetItem
      - dynamodb:Query
      - dynamodb:Scan
    resource: "!Output TableArn"
    purpose: "Read/write operations on the passengers table"
```

---

**4. Freeform stack naming vs. convention-computed name**

```yaml
# WRONG
stack_name: "my-dynamodb-table"
```

```yaml
# CORRECT
stack_name: "{APP_NAMESPACE}-{APP_ENV}-ddb"
```

---

**5. Runtime template modification vs. immutable bundled template**

```markdown
# WRONG
If the table needs a secondary index, add a GlobalSecondaryIndex
resource to template.yml before deploying.
```

```markdown
# CORRECT
The template includes a GlobalSecondaryIndex.
The index configuration is controlled by parameters:
  - GsiHashKeyName (default: none — set to enable)
  - GsiRangeKeyName (optional)
If no GSI is needed, leave GsiHashKeyName empty.
```

---

**6. "Deploy and check" vs. plan-validate-execute**

```markdown
# WRONG
Deploy the stack. If it fails, check the error and try again.
```

```markdown
# CORRECT
1. Check stack state:
   aws cloudformation describe-stacks --stack-name {name} --query 'Stacks[0].StackStatus'
2. If ROLLBACK_COMPLETE: delete and recreate (see TROUBLESHOOT.md).
3. If *_COMPLETE: proceed with update.
4. If *_IN_PROGRESS: wait for completion before proceeding.
5. Deploy:
   uv run deploy cfn --stack-name {name} --template template.yml ...
6. Verify: stack status is CREATE_COMPLETE or UPDATE_COMPLETE.
```

---

**7. Error handling by improvisation vs. cataloged recovery**

```markdown
# WRONG
If the deployment fails, diagnose the issue and take corrective action.
```

```markdown
# CORRECT
If the deployment fails, read TROUBLESHOOT.md and follow the recovery
procedure for the specific error. Do not attempt to fix the issue
without consulting the failure catalog.
```

---

**8. Verbose explanatory prose vs. concise declaration**

```markdown
# WRONG
CloudFormation is an AWS service that allows you to define infrastructure
as code. We use it to deploy a DynamoDB table. The deploy command will
create or update the stack. Make sure your credentials are configured
and you have the necessary permissions to create DynamoDB tables.
```

```markdown
# CORRECT
- **Template**: template.yml
- **Stack name**: {APP_NAMESPACE}-{APP_ENV}-ddb
- **Deploy**: `uv run deploy cfn --stack-name {name} --template template.yml`
- **Verify**: Stack status is CREATE_COMPLETE or UPDATE_COMPLETE.
```

## 9. Testing and Evaluation

The Anthropic Skill Authoring Best Practices recommend building evaluations before writing extensive documentation [2]. For resource skills, evaluation validates that the skill's metadata, templates, and security advisories produce correct infrastructure when consumed by process skills.

**Evaluation scenarios for stack skills:**

1. **Isolated deployment** — deploy the stack skill's CloudFormation template in a test account. Verify all resources are created, all outputs are populated, and the stack reaches `CREATE_COMPLETE`.
2. **Idempotent re-deployment** — deploy the same template with the same parameters. Verify the stack returns "No updates are to be performed" or reaches `UPDATE_COMPLETE` without errors.
3. **Security composition** — provide the stack skill's SECURITY.md to `/ipa.security` (or a test harness). Verify the generated IAM policy includes exactly the declared actions on the declared resources, with no additional permissions.
4. **Parameter validation** — supply invalid values for each parameter. Verify the validation pattern catches the error and the error message is displayed.
5. **Failure recovery** — force a deployment failure (e.g., invalid parameter, permission denial). Verify TROUBLESHOOT.md provides the correct detection commands and recovery procedure.

**Evaluation scenarios for pattern skills:**

1. **End-to-end composition** — compose and deploy all stacks in the pattern. Verify inter-stack wiring is correct: outputs from source stacks are received as parameters by target stacks.
2. **Wiring completeness** — verify every required parameter on every stack is wired. A missing connection should be detectable by validating WIRING.md against the stack skills' parameter and output tables.
3. **Teardown safety** — tear down the pattern in reverse order. Verify no orphaned resources remain and no deletion fails due to unresolved dependencies.
4. **Runbook accuracy** — generate a runbook from the pattern's metadata. Verify the runbook correctly describes every stack, every parameter, and every dependency.

**The Claude A/B testing pattern:**

Use one Claude instance (Claude A) to author the resource skill and a separate, fresh instance (Claude B) to test it. Give Claude B the composed skill and a deployment task. Observe where Claude B deviates from the intended path, misinterprets metadata, or encounters errors not covered by the failure catalog. Feed those observations back to Claude A to improve the skill's precision [2].

## References

1. [IPA Concept Document](../../concepts/ipa-concept.md) — High-level goals, design philosophy, stacks/patterns/composition model, security model, eject workflow, design tenets
2. [Anthropic Skill Authoring Best Practices](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices) — Official guidance on conciseness, degrees of freedom, progressive disclosure, feedback loops, anti-patterns, evaluation
3. Project Brief (`.context/aidocs.md`) — Project objectives, audience, voice and tone, principles, constraints
4. Legacy IPA Implementation — 12 legacy resource skills with procedural step-by-step patterns, state passing, error handling, troubleshooting, teardown sequences
5. Existing IPA Skills (ipa.init, ipa.security) — Validation tables, confirmation-before-write, CloudFormation deployment, `.env` management, error handling with recovery procedures
6. Speckit Command Suite — Pre-execution validation, progressive disclosure, extension hooks, handoffs, incremental state management
7. Technical Specification (`.context/aicode-technical.md`) — System architecture, data models, CloudFormation structure, stack naming convention, IAM role architecture, inter-stack data flow

## Glossary

**Builder** — the automation agent that composes and deploys patterns into a working stack [3].

**Eject** — the process of converting an automated deployment into a standalone, human-readable project that can be maintained independently [3].

**Engagement** — a consulting project or client delivery where patterns accelerate infrastructure setup [3].

**Full stack** — the complete set of infrastructure layers (compute, networking, storage, security, application) deployed by a pattern [3].

**Naming convention** — the system-wide formula for computing resource names from `APP_NAMESPACE`, `APP_ENV`, and a resource-type-specific suffix. See Section 5 for the complete reference.

**Path to production** — the journey from builder-composed infrastructure to organization-approved, production-grade deployment [3].

**Pattern** — a reusable, composable unit of infrastructure that the agent can deploy. In the context of this document, a "pattern skill" composes multiple stack skills into a deployable solution [1][3].

**Pattern skill** — a resource skill (`/ipa.pattern.*`) that composes multiple stack skills into a deployable solution by declaring the deployment sequence and inter-stack wiring. See Section 4.

**Refactor** — the process by which a client's team adapts builder output to meet their organizational standards and practices [3].

**Security advisory** — the structured metadata in a stack skill's SECURITY.md file that declares the IAM permissions and security controls required by the stack. Consumed by `/ipa.security` to compose least-privilege policies. See Section 3.7.

**Service suffix** — the fixed, short identifier used in the naming convention for a specific stack skill (e.g., `ddb` for DynamoDB, `fn` for Lambda). See Section 5.

**Stack** — a single AWS CloudFormation stack that wraps a primary service. In the IPA framework, the term refers specifically to the CloudFormation stack deployed by a stack skill [1].

**Stack skill** — a resource skill (`/ipa.stack.*`) that wraps a single AWS service with its CloudFormation template, parameters, outputs, and security metadata. The atomic building block of the IPA resource library. See Section 3.

**Wiring map** — the structured declaration in a pattern skill's WIRING.md file that specifies every output-to-input connection between stacks. See Section 4.3.
