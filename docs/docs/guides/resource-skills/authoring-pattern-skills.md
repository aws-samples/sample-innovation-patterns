# Pattern Skill Authoring Guide

## Introduction

A pattern skill is a composition contract that declares which stacks to deploy, in what order, and how their outputs wire together. It does not execute directly — the `/ipa.compose` process skill translates it into executable artifacts: Makefiles, a runbook, a composed skill, and a security disposition register [1][2][3]. The pattern skill is the blueprint; compose is the builder that reads it.

The precision of this interface determines whether composition succeeds or fails. Pattern skills are consumed mechanically by the compose skill — section headings, field formats, and dependency declarations must match the expected structure exactly. Imprecision does not produce authoring-time errors. It produces deployment-time failures, often in a different stack, with error messages that do not trace back to the root cause [2][9]. A miswired output, for example, compiles into a Makefile that passes a wrong value to a CloudFormation parameter override. The target stack deploys with an invalid ARN, and the resulting error message names the target parameter — not the source wiring entry that supplied the incorrect value.

This document covers pattern skill authoring only. Stack skill authoring (the individual `/ipa.stack.*` skills referenced by patterns), CloudFormation template design, and the internal implementation of `/ipa.compose` are out of scope. The intended audience is skill authors — both human practitioners and AI agents — who create new pattern skills or modify existing ones. Readers are expected to understand the Innovation Patterns project structure, YAML frontmatter conventions, and Makefile target semantics.

The following key terms are used throughout this document. **Pattern**: a reusable, composable unit of infrastructure that the agent can deploy. **Stack**: a single AWS CloudFormation stack wrapping a primary service. **Wiring**: the explicit declaration of how one stack's outputs connect to another stack's inputs. **Builder**: the automation agent that composes and deploys patterns into a working stack. **Eject**: the process of converting an automated deployment into a standalone, human-readable project that can be maintained independently. **Composition**: the mechanical translation of a pattern skill into executable deployment artifacts [1].

## Non-Negotiable Rules

Pattern skills occupy the lowest-freedom position in the Innovation Patterns skill library. The Anthropic Skill Authoring Best Practices describe this as the "narrow bridge with cliffs on both sides" — there is one safe path forward, and deviation produces real failures that persist in the AWS account [2][9]. These constraints are deliberate design choices for safety, not limitations.

The following rules apply to every pattern skill without exception:

- **Never improvise wiring.** Every inter-stack connection must be declared explicitly in WIRING.md with a named source output and a named target parameter or environment variable. The agent must never pass an output from an undeclared source, never invent parameter values, and never wire a connection that is not in the wiring map [2][6].

- **Declare dependencies accurately.** If a stack requires another stack's outputs, the Stack Sequence must list that dependency — even if the deployment sometimes succeeds without it. Omitting a dependency creates a race condition that surfaces intermittently and is difficult to reproduce [2][3].

- **Stop immediately on any deployment error.** Every pattern skill must include the error-first directive in the Stack Sequence section. If a CloudFormation operation returns an error, the agent must not continue to the next step. Proceeding after a failure can deploy dependent stacks against corrupted or incomplete infrastructure [2][3].

- **Declare inter-stack wiring explicitly.** No implicit connections, no prose descriptions. "Pass the relevant outputs" is never acceptable — the exact output name and exact parameter or environment variable name must be specified [2][6].

- **Ensure idempotency.** Re-composition must overwrite artifacts safely. Running `/ipa.compose` again with the same inputs must produce identical outputs, with the single exception of the Custom Dispositions section in the security disposition register, which is preserved across re-compositions [4].

- **Never include credentials or account IDs in examples.** All examples must use parameter references (`{APP_NAMESPACE}`, `{APP_ENV}`) or placeholder values [2].

The deviation risk for pattern skills is particularly high because an error in a pattern propagates through every composition that uses it. The skill author's responsibility is to eliminate every opportunity for the agent to improvise [2][9].

## Directory Structure

Every pattern skill resides in its own directory under `.claude/skills/`. The compose skill enforces a four-file directory structure as the canonical interface [2][3][5]:

```
ipa.pattern.{solution}/
  SKILL.md              # Stack sequence, wiring summary, prerequisites (~200 lines)
  WIRING.md             # Detailed output-to-input mapping (read by /ipa.compose)
  ARCHITECTURE.md       # Solution architecture for runbook generation
  TROUBLESHOOT.md       # Pattern-level failure catalog
```

Each file serves a distinct role. **SKILL.md** is the entry point — loaded into the agent's context when the skill is triggered. It contains the deployment sequence, metadata, and a human-readable wiring summary. **WIRING.md** is the machine-parseable composition interface — the compose skill reads it to generate all inter-stack connections in Makefiles. **ARCHITECTURE.md** serves both agents composing the pattern and the generated runbook, providing design rationale and an architecture diagram. **TROUBLESHOOT.md** is the failure catalog — read by the agent when deployment errors occur [2][3].

WIRING.md and ARCHITECTURE.md are enforced as pre-composition gates. Missing either file is a hard stop — the compose skill halts with an error before generating any artifacts (validation phase V2.3) [5].

Pattern skill directories do not contain a `template.yml` file. Pattern skills reference stack skills that own CloudFormation templates; they do not own templates themselves [2].

## SKILL.md Specification

SKILL.md is the entry point loaded into the agent's context when a pattern skill is triggered. All sections below are either required or optional as marked. The compose skill parses these sections mechanically — section headings, formats, and field names must match exactly [3][4].

### Frontmatter

The YAML frontmatter follows this format:

```yaml
---
name: ipa-pattern-{solution}
description: "Compose and deploy a {solution description}. Use when the user invokes
  /ipa.pattern.{solution} or when /ipa.compose selects this pattern."
---
```

The `name` field has a maximum of 64 characters. It must use the format `ipa-pattern-{solution}` with lowercase letters, numbers, and hyphens only. The `description` field has a maximum of 1024 characters. It must be written in the third person and must include both what the skill does and when to use it [2][3].

The compose skill reads frontmatter during pattern discovery to populate the pattern selection menu [4].

**Correct example:**

```yaml
---
name: ipa-pattern-react-rest-lambda
description: "Compose and deploy a React frontend with REST API backed by Lambda and
  DynamoDB. Use when the user invokes /ipa.pattern.react-rest-lambda or when
  /ipa.compose selects this pattern."
---
```

**Anti-pattern:**

```yaml
---
name: React Lambda Pattern
description: "A pattern for deploying React apps."
---
```

The anti-pattern fails on three counts: the name contains spaces and uppercase letters (must be lowercase with hyphens), the description uses fewer than the necessary details about when to invoke the skill, and the description does not describe what the pattern deploys.

### Composition Type

The Composition Type section must contain `standalone` for the current implementation [3][4][5].

```markdown
## Composition Type

standalone
```

A standalone pattern deploys a complete solution from scratch with no infrastructure prerequisites beyond the `.env` configuration file and the security stack. The compose skill reads this section to determine prerequisite verification. If the value is not `standalone`, composition halts with an error [5].

The `add-on` composition type is architecturally specified but not yet implemented in the compose skill [2]. Pattern authors should not use it but should understand the design direction: add-on patterns would extend an existing deployed pattern by declaring a base pattern and including verification steps for prerequisite stacks.

### Prerequisites

The Prerequisites section contains a bullet list of pre-conditions that must be satisfied before composition [2][3]:

```markdown
## Prerequisites

- /ipa.init completed (.env exists with IPA project variables)
- /ipa.security completed (APP_BUILDER_ROLE_ARN set in .env)
```

For standalone patterns, two prerequisites are standard: `/ipa.init` must have been completed (confirming that the `.env` file exists with the required project variables) and `/ipa.security` must have been completed (confirming that `APP_BUILDER_ROLE_ARN` is set in `.env`). Future add-on patterns would additionally require the base pattern to be deployed.

### Stack Sequence

The Stack Sequence is one of the two most critical sections in a pattern skill, alongside WIRING.md. It defines the exact deployment order and inter-stack dependencies.

The section must begin with the error-first directive [2][3]:

```markdown
> **STOP immediately if any deployment step fails. Do not continue to the next step.**
```

Each entry in the numbered list follows this exact format [3][4]:

```
{N}. Deploy **ipa.stack.{service}**. Depends on: {dependency list or none}.
```

The compose skill extracts three things from this section: **stack references** (`ipa.stack.{service}` names, used to locate stack skill files on disk), **deployment order** (the numbered list determines Makefile target ordering), and **dependencies** ("Depends on" declarations, translated to Make prerequisites) [3][4].

Dependencies translate directly to Makefile prerequisites. For example, the declaration `Depends on: ipa.stack.dynamodb outputs, ipa.stack.ecr outputs` becomes `deploy-fn: deploy-ddb deploy-ecr` in the generated deploy.mk [7]. Stacks with "Depends on: none" can deploy in parallel when `make -j` is used [3].

The Stack Sequence supports deploying the same stack skill type multiple times with distinct service suffixes. For example, two Lambda stacks — one for buffered invocation (`fn`) and one for streaming (`fn-stream`) — each appear as separate entries with their own dependencies and their own wiring entries in WIRING.md [2].

**Complete example** (from the react-rest-lambda pattern):

```markdown
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
```

This section has the lowest degrees of freedom in the entire pattern skill. The format is exact — deviations are not parsed correctly by the compose skill.

### Wiring Summary

The Wiring Summary provides a human-readable overview of inter-stack connections [2][3]:

```markdown
## Wiring Summary

DynamoDB.TableArn → Lambda (buffered + streaming) dynamodb_table_arns
Cognito.UserPoolArn → API Gateway cognito_user_pool_arn
Cognito.IssuerUrl → Lambda (buffered + streaming) env.AUTH_ISSUER
Lambda.FunctionArn → API Gateway lambda_function_arn

**Full wiring map**: See [WIRING.md](WIRING.md)
```

This section is for human orientation only. The compose skill does not parse it — it reads WIRING.md for the machine-parseable version. The Wiring Summary helps a human reader quickly understand the inter-stack data flow without parsing YAML.

### Environment Variable Contract

The Environment Variable Contract is a table of runtime values that Lambda or ECS functions receive [2][3]:

```markdown
## Environment Variable Contract

Every Lambda function in this pattern receives these environment variables:

| Variable | Source | Required |
|----------|--------|----------|
| APP_REGION | .env AWS_REGION | Yes |
| APP_ENV | .env APP_ENV | Yes |
| APP_NAMESPACE | .env APP_NAMESPACE | Yes |
| AUTH_ISSUER | ipa.stack.cognito → IssuerUrl | Yes |
| AUTH_AUDIENCE | ipa.stack.cognito → UserPoolClientId | Yes |
```

This table is distinct from deployment-time parameter wiring. Parameters wired via `target.parameter` in WIRING.md are passed through Makefile `--parameter-overrides` at deployment time. Environment variables listed here are runtime values that the deployed Lambda function receives. Both document the same connections, but the Environment Variable Contract is the consolidated view — it shows every runtime value a function needs regardless of whether it originates from `.env` or from a stack output [2][3].

The relationship to `target.env` entries in WIRING.md is direct: each `target.env` wiring entry corresponds to a row in this table where the source is a stack output.

### Teardown Sequence

The Teardown Sequence is the reverse of the deployment order [2][3][4]:

```markdown
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
```

The rationale for reverse-order deletion is structural: CloudFormation cross-stack references require dependent stacks to be deleted before the stacks they depend on. Deleting a source stack while a target stack still references its outputs causes a deletion failure [2][4].

Each step must verify `DELETE_COMPLETE` before proceeding to the next deletion. The teardown sequence must also handle partial deployments — if only stacks 1 through 4 of an 8-stack pattern were deployed, the teardown sequence skips stacks 5 through 8 [2].

### Known Deferrals (Optional)

Known Deferrals are pre-identified security findings that are accepted for proof-of-concept scope [3][4]:

```markdown
## Known Deferrals

- **DEF-001**: CloudFront HTTPS-only — custom domain SSL certificate not provisioned in POC scope
- **DEF-002**: DynamoDB backup — point-in-time recovery configured but no automated backup validation
```

Each deferral uses a `DEF-{NNN}` identifier followed by a description. The compose skill copies these entries into the security disposition register's Pattern Deferrals section [4].

The regeneration behavior is important to understand: Pattern Deferrals in the disposition register are regenerated on every compose run. Custom Dispositions (added manually after composition) are preserved across re-compositions [4]. This means pattern authors can add, remove, or modify deferrals in SKILL.md and re-compose without losing manual security findings.

Every known security gap should be documented as a deferral. Omitting a deferral does not make the gap disappear — it makes it invisible in the security disposition register.

## The Wiring Interface: WIRING.md

WIRING.md is the single source of truth for inter-stack communication and the most critical file for composition predictability [2][6][7]. Every inter-stack connection in the generated Makefiles, composed skill, and runbook originates from entries in this file. The compose skill reads WIRING.md mechanically — it does not infer connections from context, documentation, or convention.

### Format Specification

WIRING.md uses structured YAML with the following field definitions [2][6]:

| Field | Type | Description | Consumed By |
|-------|------|-------------|-------------|
| `source.stack` | String | The stack skill that produces the output. Must match a stack in the Stack Sequence. | Makefile target dependency, runbook |
| `source.output` | String | PascalCase output name as declared in the source stack skill's Output table. | Makefile `$(eval)` line |
| `target.stack` | String | The stack skill that consumes the value. | Makefile target, runbook |
| `target.parameter` | String | A CloudFormation parameter on the target stack. Mutually exclusive with `target.env`. | Makefile `--parameter-overrides` |
| `target.env` | String | An environment variable on the target stack. Mutually exclusive with `target.parameter`. | Composed skill Environment Variable Contract, runbook |
| `notes` | String | One-line explanation of the connection's purpose. | Runbook deployment section |

**Complete multi-entry example** (from the react-rest-lambda pattern):

```yaml
# Wiring Map: React REST Lambda

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

### Validation Rules

The compose skill enforces five validation rules on WIRING.md entries (validation phase V4) [2][5]:

1. **Source output must exist in the source stack's Outputs table.** The compose skill reads the referenced stack skill's SKILL.md and verifies that the named output is declared. A wiring entry referencing a nonexistent output is a hard stop.

2. **Target parameter must exist in the target stack's Parameters table.** If a `target.parameter` is specified, the compose skill verifies that the named parameter is declared in the target stack skill's Parameter table. A reference to a nonexistent parameter is a hard stop.

3. **Exactly one of `target.parameter` or `target.env` per entry.** Each wiring entry must specify either a deployment-time parameter or a runtime environment variable — never both, never neither.

4. **No circular dependencies.** The wiring map must form a directed acyclic graph (DAG). If stack A's output feeds stack B, and stack B's output feeds stack A (directly or transitively), composition halts.

5. **Every required parameter on every stack must be wired.** A stack in the sequence that has required parameters (no default value) must have wiring entries that supply values for each one. A missing connection is a hard stop.

On any validation failure, the compose skill halts without generating artifacts. The error message identifies the specific violation — which wiring entry failed, which output or parameter is missing, or which cycle was detected [5].

### Deployment-Time vs. Runtime Wiring

This distinction is critical for pattern authors. WIRING.md supports two wiring paths, and confusing them produces either deployment failures or missing runtime configuration.

**Deployment-time wiring** (`target.parameter`) passes a value through the Makefile's `--parameter-overrides` argument to CloudFormation. The compose skill generates `$(eval)` lines that capture source stack outputs using `uv run deploy cfn-outputs`, then injects the captured value as a parameter override on the target stack's deployment command [7]. The value is resolved once at deployment time and baked into the CloudFormation stack.

```makefile
# Deployment-time wiring: DynamoDB TableArn → Lambda DynamoDbTableArns
deploy-fn: deploy-ddb
	$(eval TABLE_ARN := $(shell uv run deploy cfn-outputs \
		--stack-name $(APP_NAMESPACE)-$(APP_ENV)-ddb --output-key TableArn))
	uv run deploy cfn \
		--stack-name $(APP_NAMESPACE)-$(APP_ENV)-fn \
		--template infra/cfn/lambda.yml \
		--parameter-overrides DynamoDbTableArns=$(TABLE_ARN)
```

**Runtime wiring** (`target.env`) is NOT wired in Makefiles. Instead, `target.env` entries are documented in the composed skill's Environment Variable Contract and referenced in the runbook [7]. The target stack's CloudFormation template must accept the value as a parameter and map it to a Lambda or ECS environment variable in the function or task configuration.

The ownership contract for runtime wiring is as follows: the pattern skill declares the connection (which source output feeds which target environment variable), and the stack skill's CloudFormation template is responsible for accepting that value as a parameter and mapping it to the function's environment block. This is a cross-cutting contract between the pattern WIRING.md and the stack template. The specification for this mapping is implied rather than formally documented — pattern authors should verify that each `target.env` wiring entry has a corresponding parameter-to-environment-variable mapping in the target stack's template [Research Gap].

```yaml
# Runtime wiring: Cognito IssuerUrl → Lambda AUTH_ISSUER
- source:
    stack: ipa.stack.cognito
    output: IssuerUrl
  target:
    stack: ipa.stack.lambda
    env: AUTH_ISSUER
  notes: "JWT validation at the application layer"
```

The Lambda stack's `template.yml` must contain:

```yaml
Parameters:
  AuthIssuer:
    Type: String
    Description: "Cognito issuer URL for JWT validation"

Resources:
  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      Environment:
        Variables:
          AUTH_ISSUER: !Ref AuthIssuer
```

### How Wiring Translates to Makefiles

The translation from WIRING.md YAML to deploy.mk syntax follows a mechanical, deterministic process [7]:

**WIRING.md entry:**

```yaml
- source:
    stack: ipa.stack.dynamodb
    output: TableArn
  target:
    stack: ipa.stack.lambda
    parameter: DynamoDbTableArns
  notes: "Grants Lambda read/write access to the table"
```

**Generated deploy.mk output:**

```makefile
deploy-fn: deploy-ddb
	$(eval TABLE_ARN := $(shell uv run deploy cfn-outputs \
		--stack-name $(APP_NAMESPACE)-$(APP_ENV)-ddb --output-key TableArn))
	uv run deploy cfn \
		--stack-name $(APP_NAMESPACE)-$(APP_ENV)-fn \
		--template infra/cfn/lambda.yml \
		--parameter-overrides DynamoDbTableArns=$(TABLE_ARN)
```

The translation rules are:

1. **Source output** becomes a `$(eval)` line with `uv run deploy cfn-outputs` that captures the output value from the source stack.
2. **Target parameter** becomes a `--parameter-overrides` argument on the target stack's deployment command.
3. **Dependencies** from the Stack Sequence become Make prerequisites (`deploy-fn: deploy-ddb`).
4. **Variable names** in `$(eval)` lines use UPPER_SNAKE_CASE derived from the output key name (e.g., `TableArn` becomes `TABLE_ARN`) [7].

### Anti-Patterns

The following wiring anti-patterns are the most dangerous because they do not fail at composition time — they fail at deployment time or produce silently incorrect infrastructure:

**Implicit wiring** — describing connections in prose instead of naming exact outputs and parameters:

```yaml
# WRONG
wiring:
  - source: ipa.stack.cognito
    target: ipa.stack.apigw
    description: "Pass the relevant Cognito outputs to API Gateway"

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

**Missing `notes` field** — compiles and deploys correctly but degrades the generated runbook. The runbook's deployment section uses `notes` to explain each wiring connection. Omitting it leaves the customer-facing document without an explanation of why the connection exists [2].

**Referencing a nonexistent output or parameter** — specifying an output that does not exist in the source stack's Outputs table or a parameter that does not exist in the target stack's Parameters table. This is caught by V4 validation, but the error message names the wiring entry — not the source of the author's confusion:

```yaml
# WRONG — TableARN does not exist; the correct output is TableArn (PascalCase)
- source:
    stack: ipa.stack.dynamodb
    output: TableARN
  target:
    stack: ipa.stack.lambda
    parameter: DynamoDbTableArns

# CORRECT
- source:
    stack: ipa.stack.dynamodb
    output: TableArn
  target:
    stack: ipa.stack.lambda
    parameter: DynamoDbTableArns
```

## ARCHITECTURE.md Specification

ARCHITECTURE.md serves a dual purpose: it provides context for agents composing the pattern and it supplies content for the generated runbook's architecture section [2]. This is the one area within a pattern skill where higher degrees of freedom are appropriate. Design rationale, problem framing, and comparison of alternatives are all valid content [2].

**Required content:**

1. **Problem statement** — a description of the use case this pattern addresses, in one to two paragraphs.
2. **Architecture diagram** — an ASCII or Mermaid diagram showing the stack dependency graph and data flow.
3. **Stack-by-stack summary** — what each stack contributes to the solution, presented as a table or list.
4. **Alternatives considered** — why this composition was chosen over other approaches (optional but recommended).

The compose skill copies ARCHITECTURE.md verbatim into the runbook [4][10]. Because the runbook audience is a customer's engineering team — not IPA skill authors — the ARCHITECTURE.md must be self-contained. It must not reference IPA terminology, skill names, or the AI agent. A customer engineer reading the runbook should understand the architecture without any Innovation Patterns context.

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

**Example stack-by-stack summary:**

| Stack | Role |
|-------|------|
| DynamoDB | Application data store — provides table ARN and name to Lambda functions |
| ECR | Container image registry — stores Lambda deployment packages |
| Cognito | Authentication — issues JWTs validated by API Gateway and Lambda |
| Lambda (buffered) | Request-response API handler — reads/writes DynamoDB |
| Lambda (streaming) | Event-driven processor — reads DynamoDB streams |
| API Gateway | REST API endpoint — routes requests to Lambda, enforces Cognito auth |
| S3 | Static asset hosting — serves the React frontend |
| CloudFront | CDN — unified entry point routing static assets and API requests |

## TROUBLESHOOT.md Specification

Every pattern skill must include a TROUBLESHOOT.md file that maps failure symptoms to detection commands and exact recovery procedures. The agent reads this file when deployment errors occur [2].

The format for each failure mode is: **symptom** (what the operator observes), **cause** (why it happened), **detection** (how to confirm the diagnosis), and **recovery** (exact commands to resolve it).

Three standard failure modes must be covered in every pattern skill [2]:

1. **ROLLBACK_COMPLETE** — a stack creation failed and CloudFormation rolled back all resources.
2. **Permission Denied** — the execution role lacks a required IAM permission.
3. **Resource Already Exists** — a resource with the same name exists outside this stack.

Pattern-level troubleshooting covers inter-stack issues — dependency ordering failures, wiring mismatches, and cross-stack reference errors. Stack-level failures (e.g., a malformed CloudFormation template) are documented in the individual stack skill's TROUBLESHOOT.md.

**Example failure mode template:**

```markdown
## Dependency Ordering Failure

**Symptom**: Target stack deployment fails with "Parameter {ParamName} value is invalid"
  or "No export named {ExportName} found".
**Cause**: A source stack has not completed deployment, or the wiring references an
  output that does not exist on the source stack.
**Detection**:
  1. Verify the source stack reached CREATE_COMPLETE or UPDATE_COMPLETE:
     ```bash
     aws cloudformation describe-stacks \
       --stack-name {APP_NAMESPACE}-{APP_ENV}-{source_suffix} \
       --query 'Stacks[0].StackStatus' \
       --output text --region {AWS_REGION} --profile {AWS_PROFILE}
     ```
  2. Verify the expected output exists:
     ```bash
     uv run deploy cfn-outputs \
       --stack-name {APP_NAMESPACE}-{APP_ENV}-{source_suffix} \
       --output-key {OutputName}
     ```
**Recovery**:
  1. If the source stack is not deployed: deploy it first (check Stack Sequence ordering).
  2. If the output does not exist: verify WIRING.md output name matches the source
     stack skill's Outputs table exactly (case-sensitive).
  3. Re-run the failed deployment step.
```

## Naming Conventions

Stack names follow a system-wide invariant: `{APP_NAMESPACE}-{APP_ENV}-{service_suffix}` [2][8]. This formula governs every stack name in every Makefile, every runbook, every security policy, and every cross-stack reference in the Innovation Patterns framework. Deviation breaks composition.

Each stack skill owns a unique service suffix registered in a central registry [2]:

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

In pattern skills, service suffixes appear in three places: the Stack Sequence (to identify which stack deploys where), WIRING.md (to connect outputs to inputs via stack references), and implicitly in the Teardown Sequence (reverse of deployment). Consistency across all three is a compose-time validation requirement.

The compose skill validates suffix uniqueness across all stacks in a pattern (validation phase V3.4) [5]. No two stacks in a single pattern may share a suffix. When creating a new stack skill, the skill author must register its suffix in the service suffix registry before any pattern can reference it.

The suffix registry is currently a documentation table, not a machine-enforced artifact. Two authors working independently could assign the same suffix to different stack skills and not discover the collision until both stacks appear in the same pattern. Pattern authors should check the registry manually before assigning new suffixes [Research Gap].

## How Compose Consumes Pattern Skills

This section describes what the compose skill reads from pattern skills, what it validates, and what it generates. The internal implementation of the compose skill is out of scope — this section focuses on what the pattern author needs to know to write a pattern that composes correctly [4][5][6].

### Validation Chain (V2-V4)

The compose skill performs three validation phases relevant to pattern authors before generating any artifacts [5]:

| Phase | Scope | What It Checks |
|-------|-------|----------------|
| V2: Pattern Skill | Structure and completeness | Required sections exist (Composition Type, Stack Sequence). Related files exist (WIRING.md, ARCHITECTURE.md). Composition Type is `standalone`. Stack Sequence references at least one stack. |
| V3: Stack Skills | Referenced stacks | For each stack referenced in the sequence: SKILL.md exists, required sections exist (CloudFormation Contract, Parameters, Outputs), CloudFormation template exists on disk, no suffix collisions across stacks. |
| V4: Wiring Map | Inter-stack connections | For each WIRING.md entry: source output exists in source stack's Outputs table, target parameter exists in target stack's Parameters table (if `target.parameter`), exactly one of parameter/env per entry, no circular dependencies, every required parameter on every stack is wired. |

The validation chain operates as a contract: if a pattern passes V2 through V4, it will compose correctly. If it fails, the error message identifies the specific violation — which section is missing, which file does not exist, which output reference is invalid [5].

Some checks are structural and are caught automatically by validation. Others are quality checks that the compose skill does not enforce. For example, "every wiring entry has a `notes` field" is not validated — a missing `notes` field does not block composition but degrades the runbook [2].

### Generated Artifacts

The compose skill reads pattern and stack skills and generates six artifacts [4][6]:

| Artifact | Location | Pattern Metadata That Feeds It |
|----------|----------|-------------------------------|
| Composed pattern skill | `.claude/skills/ipa.composed.{pattern}.md` | Stack Sequence, Wiring Summary, Environment Variable Contract |
| Deploy Makefile | `scripts/deploy.mk` | Stack Sequence (targets, dependencies), WIRING.md (output capture, parameter overrides) |
| Build Makefile | `scripts/build.mk` | Stack skills' Build Requirements sections |
| Test Makefile | `scripts/test.mk` | Stack skills' test and lint targets |
| Runbook | `docs/infra/runbook.md` | ARCHITECTURE.md (verbatim), Stack Sequence, WIRING.md `notes` fields, Teardown Sequence |
| Disposition register | `docs/infra/security-disposition.md` | Known Deferrals |

Artifact generation is deterministic: given the same pattern skill, stack skills, and `.env`, the compose skill produces identical output. Re-composition overwrites all artifacts except the Custom Dispositions section of the disposition register, which is preserved [4][6].

Pattern authors should understand this artifact chain because it determines what metadata matters for each downstream deliverable. If a `notes` field is missing from a WIRING.md entry, the runbook's deployment section lacks the explanation of why that connection exists. If ARCHITECTURE.md omits a diagram, the runbook's architecture section is incomplete. The metadata quality of the pattern skill directly determines the quality of the customer deliverable [2].

### Dual-Audience Design

Every piece of pattern skill metadata serves two consumers: the AI agent, which reads SKILL.md sections and WIRING.md to execute composition mechanically, and the runbook, which is generated by compose and read by a customer's engineering team to understand and deploy infrastructure independently [2].

The following table identifies which metadata fields serve which audience:

| Consumer | Fields |
|----------|--------|
| Agent only | Frontmatter (`name`, `description`), Composition Type |
| Agent + Runbook | Stack Sequence, WIRING.md (`source`, `target`), Teardown Sequence |
| Runbook only | WIRING.md `notes` fields, Environment Variable Contract descriptions, ARCHITECTURE.md content |

The consequence is that omitting `notes`, descriptions, or ARCHITECTURE.md content does not break composition — the agent does not require these fields to generate Makefiles. However, their absence degrades the customer deliverable. The runbook must be self-contained, with no references to IPA skills, Claude Code, or the AI agent [4][10]. A customer engineer reading the runbook should understand the architecture, deployment order, dependencies, and troubleshooting without any Innovation Patterns context. The richness of the pattern skill's metadata determines whether the runbook meets that standard [2].

## Anti-Patterns and Correct Patterns

AI agents pattern-match examples more reliably than they interpret abstract rules [9]. The following pairs demonstrate the most common and most dangerous authoring mistakes alongside their correct alternatives.

---

**1. Implicit wiring vs. explicit wiring**

```yaml
# WRONG — prose description, no named outputs or parameters
wiring:
  - source: ipa.stack.cognito
    target: ipa.stack.apigw
    description: "Pass the relevant Cognito outputs to API Gateway"
```

```yaml
# CORRECT — exact output, exact parameter, purpose note
wiring:
  - source:
      stack: ipa.stack.cognito
      output: UserPoolArn
    target:
      stack: ipa.stack.apigw
      parameter: CognitoUserPoolArn
    notes: "Cognito authorizer configuration"
```

**Risk**: The agent interprets "relevant outputs" differently each time. Composition may succeed, but the wrong output may be wired to the wrong parameter.

---

**2. Missing dependencies in Stack Sequence vs. accurate dependency declaration**

```markdown
# WRONG — Lambda has no declared dependency on DynamoDB
4. Deploy **ipa.stack.lambda**. Depends on: ipa.stack.ecr outputs.
```

```markdown
# CORRECT — all dependencies declared
4. Deploy **ipa.stack.lambda**. Depends on: ipa.stack.dynamodb outputs, ipa.stack.ecr outputs.
```

**Risk**: Without the DynamoDB dependency, the Makefile does not establish a prerequisite. Under `make -j` (parallel execution), Lambda may deploy before DynamoDB completes, causing the `$(eval)` output-capture command to fail or return empty.

---

**3. Freeform stack naming vs. convention-computed names**

```yaml
# WRONG — hardcoded name
stack_name: "my-dynamodb-table"
```

```yaml
# CORRECT — convention-computed name
stack_name: "{APP_NAMESPACE}-{APP_ENV}-ddb"
```

**Risk**: Hardcoded names break in every environment except the one they were written for. Cross-stack references, security policies, and the eject workflow all depend on the naming convention.

---

**4. Deployment-first ("deploy and check") vs. plan-validate-execute**

```markdown
# WRONG
Deploy all stacks. If any fail, check the error and try again.
```

```markdown
# CORRECT
> **STOP immediately if any deployment step fails. Do not continue to the next step.**

1. Deploy **ipa.stack.dynamodb**. Depends on: none.
2. Deploy **ipa.stack.ecr**. Depends on: none.
3. Deploy **ipa.stack.lambda**. Depends on: ipa.stack.dynamodb outputs, ipa.stack.ecr outputs.
```

**Risk**: Continuing after a failure deploys dependent stacks against corrupted or incomplete infrastructure. The resulting errors are difficult to trace back to the original failure.

---

**5. Vague Known Deferrals vs. specific deferral IDs with rationale**

```markdown
# WRONG
## Known Deferrals

- Some security items are deferred for POC
- HTTPS not fully configured
```

```markdown
# CORRECT
## Known Deferrals

- **DEF-001**: CloudFront HTTPS-only — custom domain SSL certificate not provisioned in POC scope
- **DEF-002**: DynamoDB backup — point-in-time recovery configured but no automated backup validation
```

**Risk**: Vague deferrals cannot be tracked or resolved. The disposition register requires specific IDs for traceability. A deferral without a rationale cannot be evaluated for production readiness.

## Quality Validation Checklist

The following checklist is a pattern-skill-specific subset of the quality standards from the authoring resource skills guide (Section 7) [2]. It should be completed before submitting a pattern skill for composition.

Items marked **(Auto)** are validated by the compose skill's V2-V4 checks. Items marked **(Manual)** require the pattern author to verify.

### Structure

- [ ] All four files are present: SKILL.md, WIRING.md, ARCHITECTURE.md, TROUBLESHOOT.md **(Auto — V2.3)**
- [ ] SKILL.md body is under 250 lines **(Manual)**
- [ ] Frontmatter `name` follows `ipa-pattern-{solution}` format **(Manual)**
- [ ] Frontmatter `description` is under 1024 characters, third person, includes what and when **(Manual)**
- [ ] Required sections exist: Composition Type, Stack Sequence, Prerequisites **(Auto — V2)**

### Stack Sequence

- [ ] Error-first directive is present at the top of the section **(Manual)**
- [ ] Every entry follows exact format: `{N}. Deploy **ipa.stack.{service}**. Depends on: {deps}.` **(Manual)**
- [ ] At least one stack is referenced **(Auto — V2)**
- [ ] All declared dependencies are accurate — no missing dependencies **(Manual)**

### Wiring

- [ ] Every `source.output` exists in the source stack's Outputs table **(Auto — V4)**
- [ ] Every `target.parameter` exists in the target stack's Parameters table **(Auto — V4)**
- [ ] Exactly one of `target.parameter` or `target.env` per entry **(Auto — V4)**
- [ ] No circular dependencies **(Auto — V4)**
- [ ] Every required parameter on every stack is wired **(Auto — V4)**
- [ ] Every wiring entry has a `notes` field **(Manual)**
- [ ] `target.env` entries have corresponding parameter-to-env mappings in the target stack's template **(Manual)**

### Naming

- [ ] All stack references use registered service suffixes **(Manual)**
- [ ] Suffixes are consistent across Stack Sequence, WIRING.md, and Teardown Sequence **(Manual)**
- [ ] No suffix collisions within the pattern **(Auto — V3.4)**

### Eject / Runbook

- [ ] ARCHITECTURE.md includes a diagram and stack-by-stack summary **(Manual)**
- [ ] ARCHITECTURE.md is self-contained — no IPA terminology or agent references **(Manual)**
- [ ] Every wiring `notes` field is meaningful (not empty or placeholder) **(Manual)**
- [ ] Teardown Sequence is exact reverse of deployment order **(Manual)**

## Sources

1. [IPA Concept Document](../../getting-started/concepts/ipa-concept.md) — foundational concepts: stacks, patterns, composition model, builder workflow, design tenets
2. [Authoring Resource Skills Guide](../../guides/authoring-resource-skills.md) — structural specification for stack and pattern skills, directory structure, templates, quality checklist, anti-patterns
3. [Pattern Skill Input Format Contract](../../../specs/003-ipa-compose-skill/contracts/pattern-skill-format.md) — parse requirements for pattern SKILL.md sections and related files
4. [IPA Compose Skill (SKILL.md)](../../../.claude/skills/ipa.compose/SKILL.md) — the implemented compose skill's workflow showing how pattern skills are consumed
5. [Compose Validation Procedures (VALIDATION.md)](../../../.claude/skills/ipa.compose/VALIDATION.md) — V1-V4 pre-composition validation checks
6. [Compose Data Model](../../../specs/003-ipa-compose-skill/data-model.md) — input/output entity definitions, field types, validation rules, state transitions
7. [Deploy Makefile Format Contract](../../../specs/003-ipa-compose-skill/contracts/deploy-makefile-format.md) — exact Makefile syntax patterns and wiring translation rules
8. [Technical Specification](.context/aicode-technical.md) — system architecture, CloudFormation structure, stack naming convention, inter-stack data flow
9. [Resource Skills vs. Process Skills](../../getting-started/concepts/resource-process-skill-concept.md) — the resource/process taxonomy, consumption model, degrees of freedom framework
10. [Runbook Generation Template (RUNBOOK_TEMPLATE.md)](../../../.claude/skills/ipa.compose/RUNBOOK_TEMPLATE.md) — section structure for generated runbooks
