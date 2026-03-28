# Pattern and Stack Skill Authoring Guidance

This document provides authoring guidance for two skill types in the Innovation Patterns Agent (IPA): **stack skills** and **pattern skills**. A stack skill is a declarative metadata document that describes a single CloudFormation stack — its parameters, outputs, security requirements, and troubleshooting procedures. A pattern skill is a composition blueprint that declares how multiple stack skills connect into a deployable architecture. Neither skill type contains executable code; both are Markdown documents consumed by `/ipa.compose` to generate deployment artifacts [3].

The composition pipeline operates as follows: stack skills and pattern definitions are inputs to `/ipa.compose`, which reads their metadata and produces five artifacts — three Makefiles (`deploy.mk`, `build.mk`, `test.mk`), an infrastructure runbook, and a security disposition register [11]. The `/ipa.deploy` skill then executes those Makefiles against AWS CloudFormation [12]. Skill authors do not need to understand the full compose pipeline, but they must produce skills that conform to the contracts compose expects.

This document covers stack skill authoring and pattern skill authoring only. For guidance on writing process skills (imperative instruction documents executed step-by-step by the agent), refer to the IPA Process Skill Guidance document [14].

## Stack Skill Authoring

A stack skill describes a single infrastructure component — an ECR repository, a Cognito user pool, a Lambda function, or any other AWS resource group that deploys as one CloudFormation stack. The compose skill is the sole machine consumer of stack skill metadata [3].

### Directory Structure and Files

Every stack skill consists of three files in a dedicated directory [1] [2]:

```
.claude/skills/ipa.stack.{service}/
├── SKILL.md          # Composition contract (parameters, outputs, CloudFormation contract)
├── SECURITY.md       # IAM permissions, security controls, known deferrals
└── TROUBLESHOOT.md   # Failure catalog with symptom, root cause, and recovery
```

| File | Role |
|------|------|
| SKILL.md | The composition contract. `/ipa.compose` machine-reads this file to extract template paths, parameters, outputs, and build requirements. |
| SECURITY.md | The security advisory. Documents IAM permissions required for deployment and runtime, security controls enforced by the template, and known deferrals. |
| TROUBLESHOOT.md | The failure catalog. Consumed by `/ipa.deploy` during failure diagnosis and by human operators during manual deployment. |

### SKILL.md

SKILL.md is the primary file in a stack skill. It contains the metadata that `/ipa.compose` extracts during composition. The following sections describe each required and optional component.

#### Frontmatter

Every SKILL.md begins with YAML frontmatter:

```yaml
---
name: ipa-stack-{service}
description: "One-line description of what this stack deploys and who consumes its outputs."
---
```

The `name` field uses the `ipa-stack-{service}` convention with hyphens, not dots [1] [2]. The `description` field appears in skill discovery and should state both what the stack provides and what consumes it. For example, the ECR stack skill description reads: "Deploy an ECR repository for container image storage" [1].

#### CloudFormation Contract

The `## CloudFormation Contract` section declares the stack's deployment identity. Compose extracts these fields verbatim for deploy.mk target generation, and validation V3.2 checks that this section exists [6].

```markdown
## CloudFormation Contract

- **Template**: `infra/cfn/{service}/{service}.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-{suffix}`
- **Capabilities**: none
```

Three fields are required:

| Field | Convention | Notes |
|-------|-----------|-------|
| Template | `infra/cfn/{service}/{service}.yml` | Path to the CloudFormation template, relative to the project root. Validation V3.3 checks that this file exists on disk [6]. |
| Stack name | `{APP_NAMESPACE}-{APP_ENV}-{suffix}` | The suffix is a short lowercase identifier unique across the entire composition. Validation V3.4 checks suffix uniqueness [6]. |
| Capabilities | `none` or `CAPABILITY_NAMED_IAM` | Set to `CAPABILITY_NAMED_IAM` if the template creates IAM resources. Compose adds `--capabilities CAPABILITY_NAMED_IAM` to the deploy target when specified [7]. |

#### Parameters

The `## Parameters` section declares every parameter the CloudFormation template accepts. Compose reads this table during wiring resolution to determine which parameters can receive values from other stacks' outputs [3] [7].

```markdown
## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `dev \| staging \| prod` | "Must be dev, staging, or prod" |
```

Parameters fall into two categories:

- **Configuration parameters** are sourced from `.env` or hardcoded defaults. `Namespace` and `Environment` are configuration parameters that every stack must include. Compose excludes these from wiring resolution — they always receive their values from `$(APP_NAMESPACE)` and `$(APP_ENV)` [7].

- **Wirable parameters** receive their values from another stack's outputs during composition. Any parameter that is not `Namespace` or `Environment` is a wirable candidate. When compose encounters a wirable parameter, it searches all stacks' outputs for an exact name match [3].

For a stack with no cross-stack dependencies, all parameters are configuration type. The skill should note this explicitly [1] [2]:

```markdown
All parameters are **Configuration** type — sourced from `.env` or defaults. No wirable parameters from other stacks.
```

For a stack with cross-stack dependencies, the wirable parameters appear alongside the configuration parameters. Consider a hypothetical Lambda function stack that consumes ECR's output:

```markdown
## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace" |
| Environment | String | — | `dev \| staging \| prod` | "Must be dev, staging, or prod" |
| RepositoryUri | String | — | — | "ECR repository URI required" |

**Configuration** parameters: Namespace, Environment (from `.env`).
**Wirable** parameters: RepositoryUri (from ipa.stack.ecr output).
```

In this example, compose auto-wires `RepositoryUri` because the ECR stack exports an output with the same name [3]. The naming match is exact — `RepositoryUri` in the parameter table must match `RepositoryUri` in the source stack's output table for auto-wiring to succeed.

#### Outputs

The `## Outputs` section declares the values this stack exposes to downstream stacks and operators. Output names are the composability API — compose uses exact name matching for auto-wiring [3] [7].

```markdown
## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| RepositoryUri | ECR repository URI for container images | `{StackName}-RepositoryUri` | ipa.stack.lambda-fn (ImageUri) |
| RepositoryArn | ECR repository ARN for security policy scoping | `{StackName}-RepositoryArn` | Security policy scoping |
```

| Column | Purpose |
|--------|---------|
| Output | The CloudFormation output key name. This name is what compose uses for wiring — choose names that match downstream stacks' parameter names to enable auto-wiring [7]. |
| Description | Human-readable description of the output value. |
| Export Convention | The CloudFormation Export name, following the `{StackName}-{OutputName}` convention [8]. |
| Used By | Lists consuming stack skills and their parameter names (e.g., "ipa.stack.lambda-fn (ImageUri)"). This column is documentation-only — compose does not read it [1]. However, it is critical for human understanding of the dependency graph. |

When naming outputs, consider the downstream stacks that will consume them. If a Lambda stack will have a parameter named `RepositoryUri`, name the ECR output `RepositoryUri` to enable auto-wiring. Mismatched names require explicit wiring declarations in the pattern's PATTERN.md [3].

#### Build Requirements (Optional)

The `## Build Requirements` section declares build steps that compose should generate in `build.mk`. If the stack has no build step (the stack is CloudFormation-only), omit this section entirely [7].

Two build types are supported:

**Container builds** generate a `build-{function}` target that builds a Docker image:

```markdown
## Build Requirements

| Type | Name | Command |
|------|------|---------|
| container | api-handler | `uv run --project utils build docker --tag $(APP_NAMESPACE)-$(APP_ENV)-api-handler` |
```

**Frontend builds** generate a `build-frontend` target that compiles a frontend application:

```markdown
## Build Requirements

| Type | Name | Command |
|------|------|---------|
| frontend | frontend | `cd frontend && npm ci && npm run build` |
```

Compose reads this section and generates the corresponding Make target in `scripts/build.mk` [7].

#### Security Summary

The `## Security Summary` section provides a brief overview of the stack's security posture with a reference to the full SECURITY.md advisory [1] [2].

```markdown
## Security Summary

**Required IAM actions**: {service}:{Action1}, {Action2}, ... — scoped to `arn:aws:{service}:{Region}:{AccountId}:resource/*`
**Security controls**: {Brief list of enforced controls}
**Full advisory**: See [SECURITY.md](SECURITY.md)
```

This section is for human reference. Compose reads SECURITY.md directly for known deferrals, not this summary.

### CloudFormation Template Conventions

Each stack skill pairs with a CloudFormation template at `infra/cfn/{service}/{service}.yml` [8]. The template and the skill's SKILL.md must stay synchronized — template parameters mirror the skill's Parameters table, and template outputs mirror the Outputs table.

Template skeleton:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: '{One-line description matching SKILL.md description}'

Parameters:
  Namespace:
    Type: String
    AllowedPattern: '^[a-z][a-z0-9-]{0,11}$'
    ConstraintDescription: 'Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter'
    Description: 'Namespace prefix for resource names'

  Environment:
    Type: String
    AllowedValues: ['dev', 'staging', 'prod']
    Description: 'Deployment environment'

  # Add wirable parameters here (if any)

Resources:
  # Stack resources — one stack, one concern.
  # Resource names use: !Sub '${Namespace}-${Environment}-{service}'
  MyResource:
    Type: 'AWS::{Service}::{Resource}'
    Properties:
      # ...

Outputs:
  MyOutput:
    Description: '{Description matching SKILL.md Outputs table}'
    Value: !GetAtt MyResource.{Attribute}
    Export:
      Name: !Sub '${AWS::StackName}-MyOutput'
```

The following conventions apply to all templates:

1. **Parameters mirror the skill's Parameters table.** Each parameter has a `Type`, `AllowedPattern` or `AllowedValues` (matching the Validation column), and a `ConstraintDescription` (matching the Error Message column) [8].

2. **Resource names use `!Sub '${Namespace}-${Environment}-{service}'`.** This produces stack-scoped names that are unique per project and environment [8].

3. **Output exports use `!Sub '${AWS::StackName}-{OutputName}'`.** This matches the `{StackName}-{OutputName}` convention documented in the skill's Outputs table [8].

4. **Templates are minimal.** Each template contains only the resources for its stack. Cross-stack references are handled by compose wiring through Makefile `$(eval)` lines, not by CloudFormation `Fn::ImportValue` [8].

## Security Advisory (SECURITY.md)

Every stack skill includes a SECURITY.md file that documents the stack's security posture in structured YAML format [9] [10]. This file has four required sections.

### Deployment Permissions

The `## Deployment Permissions` section lists every IAM action required by the Builder Execution Role to create, update, and delete the stack's resources.

```yaml
## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the {service} stack.

```yaml
permissions:
  - actions:
      - {service}:CreateResource
      - {service}:DeleteResource
      - {service}:DescribeResource
      - {service}:TagResource
    resource: "arn:aws:{service}:{AWS_REGION}:{AWS_ACCOUNT_ID}:{resource-type}/{APP_NAMESPACE}-{APP_ENV}-{suffix}"
    purpose: "CloudFormation CRUD operations on {resource} resource"
```

Resource ARNs use template variables (`{AWS_REGION}`, `{AWS_ACCOUNT_ID}`, `{APP_NAMESPACE}-{APP_ENV}-{suffix}`) rather than literal values [9]. Where resource-level scoping is not possible due to AWS API limitations, set `resource: "*"` and document the reason:

```yaml
  - actions:
      - ecr:GetAuthorizationToken
    resource: "*"
    purpose: "Required for ECR authentication — this action does not support resource-level permissions (AWS API limitation)"
```

### Runtime Permissions (Advisory)

The `## Runtime Permissions (Advisory)` section documents IAM actions needed by consuming stacks at runtime, not by the Builder Role [9] [10]. These inform downstream stack authors about what their execution roles require.

```yaml
## Runtime Permissions (Advisory)

IAM actions needed by consuming stacks at runtime. These are **not** consumed by the
Builder Execution Role — they are advisory for stacks that integrate with {service}.

```yaml
runtime_permissions:
  - actions:
      - {service}:ReadAction
      - {service}:WriteAction
    resource: "!Output {OutputName}"
    purpose: "Runtime {operation} by consuming {consumer} execution roles"
```

The `resource` field uses `!Output {OutputName}` as a reference to the stack's output, indicating that the ARN is dynamic and resolved from the deployed stack.

### Security Controls

The `## Security Controls` section documents the non-configurable security posture enforced by the CloudFormation template [9] [10]. These are deliberate design choices, not parameters.

```yaml
## Security Controls

Controls enforced by the CloudFormation template. These are not configurable —
they are hardcoded security posture.

```yaml
controls:
  - type: encryption
    enabled: true
    method: "Description of encryption approach"

  - type: access_control
    enabled: true
    method: "Description of access restrictions"

  - type: deletion_safety
    enabled: true
    method: "Description of deletion protection mechanism"
```

Each control has three fields: `type` (a category such as `encryption`, `access_control`, `deletion_safety`, `advanced_security`, `authentication`, `user_creation`, or `token_security`), `enabled` (always `true` for enforced controls), and `method` (a description of the specific mechanism) [9] [10].

### Known Deferrals

The `## Known Deferrals` section documents security findings accepted for POC scope with rationale and risk level [9] [10].

```markdown
## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| {What is deferred} | {Why it is acceptable for POC scope} | {Low/Medium/High} — {mitigation or context} |
```

Compose aggregates known deferrals from all stacks in a composition into the security disposition register at `docs/infra/security-disposition.md` [3]. Each deferral must include:

- A clear description of what is deferred
- A reason explaining why the deferral is acceptable
- A risk level (Low, Medium, or High) with any mitigating factors

## Troubleshooting (TROUBLESHOOT.md)

Every stack skill includes a TROUBLESHOOT.md file that catalogs the failure modes specific to that stack [1] [2]. This file serves two consumers: the AI agent during `/ipa.deploy` failure diagnosis, and human operators during manual deployment [12].

### Failure Catalog Table

The primary structure is a table covering the most common failure scenarios:

```markdown
# Troubleshooting: ipa.stack.{service}

## Failure Catalog

| # | Scenario | Symptom | Root Cause | Recovery |
|---|----------|---------|------------|----------|
| 1 | Stack creation fails | {Exact error text or command output} | {Why it happened} | {Exact commands and steps to fix} |
| 2 | Stack deletion fails | {Exact error text or command output} | {Why it happened} | {Exact commands and steps to fix} |
| 3 | {Service-specific failure} | {Exact error text} | {Root cause} | {Recovery steps} |
```

At minimum, the failure catalog should cover:

- **Stack creation failure** — parameter validation errors, service availability issues, resource naming conflicts
- **Stack deletion failure** — resources that block deletion (e.g., non-empty ECR repositories, active user pool clients)
- **Service-specific failures** — operational failures unique to this AWS service (e.g., Docker authentication failures for ECR, domain prefix conflicts for Cognito)

Each column serves a specific purpose:

| Column | Guidance |
|--------|----------|
| Symptom | Include the exact error text or command output the operator will see. Use quoted strings or backtick-formatted text. |
| Root Cause | Explain why this failure occurs — misconfiguration, missing permission, resource conflict, or AWS service limitation. |
| Recovery | Provide exact commands to fix the issue. Include full command syntax with placeholder variables (`{APP_NAMESPACE}`, `{APP_ENV}`, etc.). |

### Additional Troubleshooting Sections

For failure modes that require more detailed explanation than a single table row, add individual sections after the table:

```markdown
## Additional Troubleshooting

### {Scenario Name}

**Symptom**: {What the operator observes}

**Root Cause**: {Detailed explanation of why this happens}

**Recovery**: {Step-by-step instructions with commands}
```

The Symptom/Root Cause/Recovery structure parallels the table format and is recognizable by both human operators and the AI agent's failure diagnosis system [12].

## Pattern Authoring

A pattern is a composition blueprint that declares how multiple stack skills connect into a deployable architecture. Patterns provide the architectural narrative that gives standalone stacks meaning — builders cannot compose individual stacks without a base pattern [3] [4].

### Directory Structure and Files

Every pattern consists of two files in a directory within the compose skill [4] [5]:

```
.claude/skills/ipa.compose/patterns/{name}/
├── PATTERN.md        # Stack sequence, wiring map, known deferrals
└── ARCHITECTURE.md   # Architecture diagram and stack inventory (copied to runbook)
```

Patterns live inside the compose skill directory (`.claude/skills/ipa.compose/patterns/`), not as standalone skill directories. This is by design — patterns are input to the compose pipeline, not independently invocable skills [4].

### PATTERN.md

PATTERN.md defines the composition: which stacks to deploy, in what order, with what connections between them. Validation V2 checks that this file contains a non-empty Stack Sequence, a Wiring section, and that an ARCHITECTURE.md file exists alongside it [6].

#### Stack Sequence

The `## Stack Sequence` section declares the deployment order as a numbered list:

```markdown
## Stack Sequence

1. ipa.stack.ecr — ECR repository for container images
   - Depends on: none
   - Suffix: ecr

2. ipa.stack.lambda-fn — Lambda function for API request handling
   - Depends on: ipa.stack.ecr
   - Suffix: lambda-fn
```

Each entry includes:

| Item | Purpose |
|------|---------|
| `ipa.stack.{service}` | References a stack skill at `.claude/skills/ipa.stack.{service}/SKILL.md`. Validation V3.1 checks that this skill exists [6]. |
| Description | Brief statement of what this stack provides in the context of the pattern. |
| `Depends on` | Lists stacks that must deploy before this one. Dependencies must reference stacks earlier in the sequence — no forward references. |
| `Suffix` | The service suffix from the stack's CloudFormation Contract. Must be unique across the entire pattern. Validation V3.4 checks this [6]. |

Position in the numbered list determines deployment order. Compose generates Make target prerequisites from the `Depends on` declarations [7].

#### Teardown Sequence

The `## Teardown Sequence` section is the exact reverse of the Stack Sequence:

```markdown
## Teardown Sequence

1. ipa.stack.lambda-fn (suffix: lambda-fn)
2. ipa.stack.ecr (suffix: ecr)
```

Compose generates the `teardown:` aggregate Make target with prerequisites in this order [7].

#### Wiring

The `## Wiring` section declares connections between stacks using a structured YAML format [3] [4]:

```markdown
## Wiring

wiring:
  - source:
      stack: ecr
      output: RepositoryUri
    target:
      stack: lambda-fn
      parameter: RepositoryUri
    notes: "Container image URI for Lambda function"
```

Each wiring entry has the following fields:

| Field | Purpose |
|-------|---------|
| `source.stack` | The service suffix of the stack that provides the output value. |
| `source.output` | The output name from the source stack's Outputs table. Validation V4.1 checks that this output exists [6]. |
| `target.stack` | The service suffix of the stack that receives the value. |
| `target.parameter` | The parameter name in the target stack's Parameters table. Validation V4.2 checks that this parameter exists [6]. Use this field for values wired via `--parameter-overrides` in deploy.mk. |
| `target.env` | Alternative to `target.parameter`. Use this field for runtime environment variables that appear in the runbook but are not wired in Makefiles [7]. Each entry must have exactly one of `target.parameter` or `target.env`, not both (V4.3) [6]. |
| `notes` | Human-readable description of what this connection does. |

Intra-pattern wiring is authoritative — compose uses it verbatim and does not auto-infer alternatives for connections declared in this section [3]. When stacks are added incrementally (outside the base pattern), compose auto-infers wiring by matching output names to parameter names. Explicit wiring in PATTERN.md takes precedence over auto-inference [3].

For a pattern with no cross-stack connections (e.g., a single-stack pattern during incremental development):

```markdown
## Wiring

wiring: []
# No wiring entries yet — downstream consumers not yet implemented.
```

#### Known Deferrals

The `## Known Deferrals` section documents pattern-level security deferrals:

```markdown
## Known Deferrals

| ID | Finding | Rationale |
|----|---------|-----------|
| DEF-001 | {Architectural decision that defers a security measure} | {Why this is acceptable for POC scope} |
```

Pattern-level deferrals cover architectural decisions (e.g., "no VPC isolation between stacks"), as opposed to stack-level deferrals in SECURITY.md that cover individual resource decisions (e.g., "no lifecycle policy on ECR repository") [4] [9].

### ARCHITECTURE.md

ARCHITECTURE.md is a free-form Markdown document that compose copies verbatim into the customer runbook [5]. It serves as the architectural narrative for the pattern.

Recommended structure:

```markdown
# Architecture: {Pattern Name}

{One-line pattern description.}

## System Architecture

{ASCII or Mermaid diagram showing layers, stacks, and connections.}

## Stack Inventory

| Stack | Layer | Purpose | Status |
|-------|-------|---------|--------|
| ipa.stack.ecr | 0 | Container image repository | **Implemented** |
| ipa.stack.lambda-fn | 1 | API request handler | Pending (Spec N) |

## Deployment Order

{Explanation of the deployment strategy — layers, parallelism, dependencies.}

## Security Model

{Summary of the pattern's security posture — IAM scoping, access controls, encryption.}

## Deployment Assumptions

{Prerequisites and environmental assumptions for deploying this pattern.}
```

One critical rule applies: ARCHITECTURE.md content must be self-contained. It must not reference IPA skills, Claude Code, or the AI agent. The runbook is a customer deliverable — a customer engineer reads it to deploy, verify, and tear down infrastructure independently [5].

### Incremental Pattern Growth

Patterns grow incrementally. A pattern starts with a subset of its planned stacks and expands as stack skills and templates are authored [5] [11]. The react-rest-lambda pattern, for example, defines 8 planned stacks in its architecture but currently has only 1 implemented [5].

The following principles govern incremental growth:

1. **The pattern must be deployable at every increment.** After each stack is added, the pattern should compose and deploy successfully. A pattern that requires all stacks to be present before it can deploy is not incrementally composable.

2. **The Stack Inventory table tracks implementation status.** Each planned stack shows either "Implemented" or "Pending (Spec N)" to communicate progress.

3. **The Wiring section grows with the pattern.** When a new stack is added, its wiring entries are appended to the existing Wiring section. Empty wiring (`wiring: []`) is valid for early increments.

4. **The Teardown Sequence expands in reverse.** Each new stack added to the Stack Sequence is also added to the front of the Teardown Sequence.

## Naming Conventions

The following table consolidates all naming conventions for stack skills, pattern skills, and their associated artifacts [1] [2] [4] [7] [8]:

| Entity | Convention | Example |
|--------|-----------|---------|
| Stack skill directory | `.claude/skills/ipa.stack.{service}/` | `.claude/skills/ipa.stack.ecr/` |
| Frontmatter name | `ipa-stack-{service}` (hyphens) | `ipa-stack-ecr` |
| CloudFormation stack name | `{APP_NAMESPACE}-{APP_ENV}-{suffix}` | `myapp-dev-ecr` |
| Service suffix | Short lowercase identifier, unique across the composition | `ecr`, `cognito`, `lambda-fn` |
| Template path | `infra/cfn/{service}/{service}.yml` | `infra/cfn/ecr/ecr.yml` |
| Output export name | `{StackName}-{OutputName}` | `myapp-dev-ecr-RepositoryUri` |
| Pattern directory | `.claude/skills/ipa.compose/patterns/{name}/` | `patterns/react-rest-lambda/` |
| Make deploy target | `deploy-{suffix}` | `deploy-ecr` |
| Make teardown target | `teardown-{suffix}` | `teardown-ecr` |
| Make build target | `build-{name}` (from Build Requirements) | `build-api-handler` |

## Validation Reference

Before invoking `/ipa.compose`, skill authors can verify their work against the validation checks that compose performs. A skill that passes these checks will compose successfully [6].

### Stack Skill Validation (V3)

| Check | What Compose Validates | How to Fix |
|-------|----------------------|------------|
| V3.1 | `.claude/skills/ipa.stack.{service}/SKILL.md` exists on disk | Create the file with required sections |
| V3.2 | SKILL.md contains `## CloudFormation Contract`, `## Parameters`, and `## Outputs` sections | Add missing sections — exact heading text matters |
| V3.3 | CloudFormation template exists at the path declared in CloudFormation Contract | Create the template at `infra/cfn/{service}/{service}.yml` |
| V3.4 | Service suffix is unique across all stacks in the pattern | Change the suffix in CloudFormation Contract to a unique value |

### Pattern Validation (V2)

| Check | What Compose Validates | How to Fix |
|-------|----------------------|------------|
| V2.2 | Stack Sequence references at least one stack | Add at least one `ipa.stack.{service}` entry to the Stack Sequence |
| V2.3 | PATTERN.md contains a `## Wiring` section and ARCHITECTURE.md exists | Add the Wiring section (can be `wiring: []`) and create ARCHITECTURE.md |

### Wiring Validation (V4)

| Check | What Compose Validates | How to Fix |
|-------|----------------------|------------|
| V4.1 | Each `source.output` exists in the source stack's `## Outputs` table | Correct the output name or add the missing output to the source stack |
| V4.2 | Each `target.parameter` exists in the target stack's `## Parameters` table | Correct the parameter name or add the missing parameter to the target stack |
| V4.3 | Each wiring entry has exactly one of `target.parameter` or `target.env` | Specify one target type per entry, not both |
| V4.4 | No circular dependencies exist in the wiring graph | Restructure dependencies so the graph is acyclic |

### Merge Validation (V5)

These checks run when stacks or patterns are added to an existing composition [6]:

| Check | What Compose Validates | How to Fix |
|-------|----------------------|------------|
| V5.1 | No duplicate suffixes across base composition and additions | Use a unique suffix for each new stack |
| V5.2 | No circular dependencies in the merged wiring graph | Review cross-composition wiring for cycles |
| V5.3 | All wired source outputs exist in their stack skills | Verify output names in source stacks |
| V5.4 | All wired target parameters exist in their stack skills | Verify parameter names in target stacks |
| V5.5 | All referenced stack skills exist on disk | Create missing stack skill directories |
| V5.6 | All referenced CloudFormation templates exist on disk | Create missing templates |

## Anti-Patterns

The following mistakes commonly cause composition failures or produce misleading artifacts.

**Mismatched output and parameter names.** If a source stack exports `RepoUri` but the consuming stack expects `RepositoryUri`, compose cannot auto-wire the connection. The wiring must then be declared explicitly in PATTERN.md. To avoid this, choose output names that match the parameter names of known consumers [3].

**Non-unique service suffixes.** Two stacks in the same composition with the suffix `api` will fail V3.4. Each stack must have a globally unique suffix within the composition. Use descriptive suffixes: `apigw` rather than `api`, `lambda-fn` rather than `lambda` [6].

**Missing required sections in SKILL.md.** Compose fails at V3.2 if `## CloudFormation Contract`, `## Parameters`, or `## Outputs` is missing. The exact heading text matters — `## CloudFormation` without "Contract" will not be recognized [6].

**Cross-stack IAM references.** Referencing another stack's IAM role ARN directly in a CloudFormation template breaks composability. Each stack should own its own IAM requirements. Cross-stack values flow through compose wiring, not through hardcoded CloudFormation references [5].

**Template parameters that diverge from the skill's Parameters table.** If the CloudFormation template has a parameter `RepoName` but the skill's Parameters table lists `RepositoryName`, compose will generate incorrect `--parameter-overrides` in deploy.mk. The template and the skill must stay synchronized [8].

**Hardcoded stack names.** Using literal stack names (e.g., `myapp-dev-ecr`) instead of the `{APP_NAMESPACE}-{APP_ENV}-{suffix}` convention prevents the stack from deploying across projects and environments. Always use the variable-based convention [1] [2].

**Secrets or real account IDs in examples.** Per project constraints, all examples must use placeholder values. Never include real AWS account IDs, ARNs, access keys, or endpoints in skill files or templates.

## Worked Example: ipa.stack.lambda-fn

This section traces a hypothetical stack skill through all files to demonstrate how the pieces connect. The example models a Lambda function stack that consumes the ECR repository URI from `ipa.stack.ecr`.

### SKILL.md

```markdown
---
name: ipa-stack-lambda-fn
description: "Deploy a Lambda function with container image from ECR. Provides function ARN and invoke URL for API Gateway integration."
---

# ipa.stack.lambda-fn

Deploy a Lambda function using a container image stored in ECR. Provides function ARN and invoke URL outputs for downstream API Gateway stacks.

## CloudFormation Contract

- **Template**: `infra/cfn/lambda-fn/lambda-fn.yml`
- **Stack name**: `{APP_NAMESPACE}-{APP_ENV}-lambda-fn`
- **Capabilities**: CAPABILITY_NAMED_IAM

## Parameters

| Parameter | Type | Default | Validation | Error Message |
|-----------|------|---------|------------|---------------|
| Namespace | String | — | `/^[a-z][a-z0-9-]{0,11}$/` | "Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter" |
| Environment | String | — | `dev \| staging \| prod` | "Must be dev, staging, or prod" |
| RepositoryUri | String | — | — | "ECR repository URI required" |

**Configuration** parameters: Namespace, Environment (from `.env`).
**Wirable** parameters: RepositoryUri (from ipa.stack.ecr output).

## Outputs

| Output | Description | Export Convention | Used By |
|--------|-------------|------------------|---------|
| FunctionArn | Lambda function ARN | `{StackName}-FunctionArn` | ipa.stack.apigw (LambdaFunctionArn) |
| FunctionName | Lambda function name | `{StackName}-FunctionName` | Operational reference |

## Build Requirements

| Type | Name | Command |
|------|------|---------|
| container | api-handler | `uv run --project utils build docker --tag $(APP_NAMESPACE)-$(APP_ENV)-api-handler` |

## Security Summary

**Required IAM actions**: lambda:CreateFunction, UpdateFunctionCode, DeleteFunction, GetFunction, TagResource — scoped to `arn:aws:lambda:{Region}:{AccountId}:function:{APP_NAMESPACE}-{APP_ENV}-*`. iam:PassRole for Lambda execution role.
**Security controls**: Reserved concurrency limits, no public function URL, VPC-optional
**Full advisory**: See [SECURITY.md](SECURITY.md)
```

### SECURITY.md

```markdown
# Security Advisory: ipa.stack.lambda-fn

## Deployment Permissions

IAM actions required by the Builder Execution Role to deploy and manage the Lambda stack.

```yaml
permissions:
  - actions:
      - lambda:CreateFunction
      - lambda:UpdateFunctionCode
      - lambda:UpdateFunctionConfiguration
      - lambda:DeleteFunction
      - lambda:GetFunction
      - lambda:TagResource
      - lambda:UntagResource
    resource: "arn:aws:lambda:{AWS_REGION}:{AWS_ACCOUNT_ID}:function:{APP_NAMESPACE}-{APP_ENV}-*"
    purpose: "CloudFormation CRUD operations on Lambda function resources"

  - actions:
      - iam:PassRole
    resource: "arn:aws:iam::{AWS_ACCOUNT_ID}:role/{APP_NAMESPACE}-{APP_ENV}-lambda-fn-exec"
    purpose: "Allow CloudFormation to assign the execution role to the Lambda function"
```

## Runtime Permissions (Advisory)

```yaml
runtime_permissions:
  - actions:
      - ecr:BatchGetImage
      - ecr:GetDownloadUrlForLayer
    resource: "!Output RepositoryArn (from ipa.stack.ecr)"
    purpose: "Runtime container image pull by Lambda execution role"
```

## Security Controls

```yaml
controls:
  - type: access_control
    enabled: true
    method: "No public function URL — Lambda is invoked only via API Gateway or internal services"

  - type: execution_role
    enabled: true
    method: "Dedicated execution role with least-privilege permissions scoped to this function"
```

## Known Deferrals

| Deferral | Reason | Risk |
|----------|--------|------|
| No VPC attachment | POC scope — Lambda runs in default networking | Low — no sensitive data access; can add VPC via parameter |
| No reserved concurrency | POC scope — sufficient for development load | Low — add for production to prevent runaway invocations |
```

### TROUBLESHOOT.md

```markdown
# Troubleshooting: ipa.stack.lambda-fn

## Failure Catalog

| # | Scenario | Symptom | Root Cause | Recovery |
|---|----------|---------|------------|----------|
| 1 | Stack creation fails | CREATE_FAILED with "iam:PassRole" error | Builder role lacks iam:PassRole permission for the Lambda execution role | Update the security stack to include iam:PassRole on the Lambda execution role ARN. Re-run `/ipa.security`. |
| 2 | Function fails to start | Lambda returns "EcrImagePullError" | ECR image does not exist or Lambda execution role lacks ecr:BatchGetImage | Build and push the container image: `make -f scripts/build.mk build-api-handler`. Verify ECR permissions in the execution role. |
| 3 | Stack deletion hangs | DELETE_IN_PROGRESS for extended period | Lambda function has active invocations or event source mappings | Wait for active invocations to drain. If persistent, manually delete event source mappings via AWS Console. |

## Additional Troubleshooting

### Image tag not found

**Symptom**: Stack update fails with "Manifest for image not found" error.

**Root Cause**: The container image tag referenced in the template does not exist in the ECR repository. This occurs when the image has not been built and pushed, or when the tag was overwritten.

**Recovery**: Build and push the image, then re-deploy:
```bash
make -f scripts/build.mk build-api-handler
make -f scripts/deploy.mk deploy-lambda-fn
```
```

### CloudFormation Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Lambda function with container image from ECR'

Parameters:
  Namespace:
    Type: String
    AllowedPattern: '^[a-z][a-z0-9-]{0,11}$'
    ConstraintDescription: 'Invalid namespace — 1-12 chars, lowercase alphanumeric + hyphens, starts with letter'

  Environment:
    Type: String
    AllowedValues: ['dev', 'staging', 'prod']

  RepositoryUri:
    Type: String
    Description: 'ECR repository URI (wired from ipa.stack.ecr)'

Resources:
  LambdaExecutionRole:
    Type: 'AWS::IAM::Role'
    Properties:
      RoleName: !Sub '${Namespace}-${Environment}-lambda-fn-exec'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: 'sts:AssumeRole'
      ManagedPolicyArns:
        - 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'

  LambdaFunction:
    Type: 'AWS::Lambda::Function'
    Properties:
      FunctionName: !Sub '${Namespace}-${Environment}-api-handler'
      PackageType: Image
      Code:
        ImageUri: !Sub '${RepositoryUri}:latest'
      Role: !GetAtt LambdaExecutionRole.Arn
      Timeout: 30
      MemorySize: 256

Outputs:
  FunctionArn:
    Description: 'Lambda function ARN'
    Value: !GetAtt LambdaFunction.Arn
    Export:
      Name: !Sub '${AWS::StackName}-FunctionArn'

  FunctionName:
    Description: 'Lambda function name'
    Value: !Ref LambdaFunction
    Export:
      Name: !Sub '${AWS::StackName}-FunctionName'
```

### Pattern Wiring

With this stack skill in place, the react-rest-lambda pattern's PATTERN.md Wiring section would declare:

```yaml
wiring:
  - source:
      stack: ecr
      output: RepositoryUri
    target:
      stack: lambda-fn
      parameter: RepositoryUri
    notes: "Container image URI for Lambda function"
```

Compose translates this wiring entry into a `$(eval)` line in deploy.mk [7]:

```makefile
deploy-lambda-fn: deploy-ecr
	$(eval REPOSITORY_URI := $(shell uv run --project utils deploy cfn-outputs \
		--stack-name $(APP_NAMESPACE)-$(APP_ENV)-ecr --output-key RepositoryUri))
	uv run --project utils deploy cfn \
		--stack-name $(APP_NAMESPACE)-$(APP_ENV)-lambda-fn \
		--template infra/cfn/lambda-fn/lambda-fn.yml \
		--parameter-overrides "Namespace=$(APP_NAMESPACE) Environment=$(APP_ENV) RepositoryUri=$(REPOSITORY_URI)" \
		--capabilities CAPABILITY_NAMED_IAM
```

The Make target `deploy-lambda-fn` depends on `deploy-ecr` (from the Stack Sequence's `Depends on` declaration), ensuring ECR deploys first. The `$(eval)` line retrieves ECR's `RepositoryUri` output at deploy time and passes it as a parameter override to the Lambda stack.

## Sources

1. [ipa.stack.ecr SKILL.md](.claude/skills/ipa.stack.ecr/SKILL.md) — ECR stack skill definition (reference implementation)
2. [ipa.stack.cognito SKILL.md](.claude/skills/ipa.stack.cognito/SKILL.md) — Cognito stack skill definition (reference implementation)
3. [ipa.compose SKILL.md](.claude/skills/ipa.compose/SKILL.md) — Compose skill that consumes stack skills and pattern definitions
4. [react-rest-lambda PATTERN.md](.claude/skills/ipa.compose/patterns/react-rest-lambda/PATTERN.md) — Pattern definition (reference implementation)
5. [react-rest-lambda ARCHITECTURE.md](.claude/skills/ipa.compose/patterns/react-rest-lambda/ARCHITECTURE.md) — Pattern architecture document
6. [VALIDATION.md](.claude/skills/ipa.compose/VALIDATION.md) — Compose validation procedures V1-V5
7. [MAKEFILE_TEMPLATES.md](.claude/skills/ipa.compose/MAKEFILE_TEMPLATES.md) — Makefile generation templates
8. [infra/cfn/ecr/ecr.yml](infra/cfn/ecr/ecr.yml) — ECR CloudFormation template (reference implementation)
9. [ipa.stack.ecr SECURITY.md](.claude/skills/ipa.stack.ecr/SECURITY.md) — ECR security advisory (reference implementation)
10. [ipa.stack.cognito SECURITY.md](.claude/skills/ipa.stack.cognito/SECURITY.md) — Cognito security advisory (reference implementation)
11. [ipa.compose as-built](docs/docs/working/specs/ipa-compose/ipa-compose-asbuilt.md) — Compose skill implementation documentation
12. [ipa.deploy as-built](docs/docs/working/specs/ipa-deploy/ipa-deploy-asbuilt.md) — Deploy skill implementation documentation
13. [009-compose-stacks spec](specs/009-compose-stacks/spec.md) — Incremental composition specification
14. [Process Skill Guidance](docs/docs/working/docs/process-skill-guidance/) — Companion document for process skill authoring
