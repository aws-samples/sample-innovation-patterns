---
title: Stack Skills vs. Pattern Skills
sidebar_position: 2
---

# Stack Skills vs. Pattern Skills

## Introduction

The Innovation Patterns Agent (IPA) organizes its infrastructure library into two tiers of resource skills: **stack skills** and **pattern skills**. A stack skill — a reusable unit that wraps a single primary AWS service — is the atomic building block of the library. A pattern skill — a composition blueprint that declares which stacks to deploy, in what order, and how their outputs connect — is the molecule that assembles those atoms into a deployable full-stack solution [1].

This two-tier architecture is the foundation of the composition model that enables reuse across engagements, automated security aggregation, and the eject workflow that produces standalone, human-readable deployment artifacts [1][3]. Understanding the distinction between stack skills and pattern skills is essential for anyone who composes, extends, or maintains the skill library.

This document defines and differentiates the two skill types, explains how they interact through the composition model, and presents the design rationale behind the separation. It does not cover step-by-step authoring instructions (reserved for the authoring guide), specific pattern or stack implementations (covered in per-pattern reference documentation), or deployment mechanics and eject workflows (documented separately) [1][2].

Readers familiar with the Resource Skills vs. Process Skills concept document will recognize that both stack skills and pattern skills fall under the "resource skill" category — they declare what infrastructure looks like, not what workflow to execute. This document goes deeper into the two tiers within that resource category [6].

## The Core Distinction

The governing relationship between the two types is structural: stack skills are infrastructure atoms; pattern skills are molecules composed from those atoms [1][2].

A **stack skill** wraps a single primary AWS service with its CloudFormation template, parameters, outputs, and security metadata. It is a self-contained, declarative unit that describes what exists after deployment — a DynamoDB table, a Lambda function, a Cognito user pool. Each stack skill is parameterized, produces typed outputs, and declares its own IAM requirements [1][2][3].

A **pattern skill** declares an ordered sequence of stack deployments with explicit output-to-input wiring, forming a deployable full-stack solution. It does not own CloudFormation templates. It references stack skills by name, specifies the order in which they deploy, and maps the outputs of one stack to the inputs of the next [1][2][4].

The following table summarizes the key differences across several dimensions:

| Dimension | Stack Skill | Pattern Skill |
|-----------|------------|---------------|
| **Primary content** | CloudFormation template + metadata | Stack sequence + wiring map |
| **Deployment unit** | Single AWS service | Full-stack solution |
| **Degrees of freedom** | Uniformly low — exact templates, validated parameters | Low to medium — fixed wiring, heuristic judgment during composition |
| **Security role** | Declares IAM actions for its service | Aggregates security declarations from referenced stacks |
| **Parameters** | Service-specific inputs with validation | Stack-to-stack output-to-input mappings |

This distinction is an authoring and composition concern, not a delivery concern. At the point of customer delivery, the two-tier hierarchy dissolves into flat Makefile targets and a runbook [1][3].

## Stack Skills

A stack skill is the atomic building block of the IPA resource library. It wraps a single primary AWS service into a self-contained, declarative metadata unit that can be consumed by any pattern skill in the library [1][2].

Stack skills are declarative: they describe what exists after deployment, not how to create it. They are non-interactive — there are no prompt sequences, no confirmation gates, and no error handling workflows. The CloudFormation template is authored once, versioned, and never modified at runtime [2][3].

### The Single-Service Boundary

The phrase "single primary AWS service" defines the identity of a stack skill, but it does not mean the stack provisions only one CloudFormation resource. A stack skill may include tightly coupled supporting resources — IAM roles, log groups, conditional resources — alongside the primary service. What matters is that all resources exist to serve that one service [1][2].

The legacy Cognito stack template illustrates this principle. Its primary resource is `AWS::Cognito::UserPool`, but the template also provisions a User Pool Client, a User Pool Domain, Managed Login Branding, an Identity Pool (conditional), two IAM roles for authenticated and unauthenticated access, and an Identity Pool Role Attachment — eight CloudFormation resource types in total. Despite this count, it remains a Cognito stack skill because every resource exists to serve the User Pool. The IAM roles are not general-purpose; they are Cognito-specific identity pool roles scoped to `cognito-identity.amazonaws.com` [5].

The following table, drawn from the legacy implementation, illustrates the range of supporting resources across different stack skills:

| Stack Directory | Primary Service | Supporting Resources |
|----------------|----------------|---------------------|
| `cognito/` | Cognito User Pool | Client, Domain, Identity Pool, IAM Roles |
| `dynamodb/` | DynamoDB Table | (minimal — table only) |
| `rest-lambda/` | Lambda Function | IAM Execution Role, Function URL, Log Group |
| `api-gateway/` | API Gateway REST API | Stage, Deployment, Cognito Authorizer |
| `s3/` | S3 Bucket | Bucket Policy, Versioning |
| `ecr/` | ECR Repository | Lifecycle Policy |
| `cloud-front/` | CloudFront Distribution | OAC, Cache Policy |
| `sqs/` | SQS Queue | Dead Letter Queue, Event Source Mapping |
| `bedrock/` | Bedrock Knowledge Base | Data Source, S3 Vectors |

The boundary is pragmatic, not formal. Supporting resources that only make sense in the context of the primary service stay inside the stack. Resources that serve multiple services — such as a VPC — receive their own stack. There is no rigid rule for when a supporting resource should remain inside versus become its own stack skill; the guiding principle is service coupling [5].

### Anatomy of a Stack Skill

Each stack skill contains four files [2][3]:

```
SKILL.md              — Parameters, outputs, security summary
template.yml          — CloudFormation template (immutable, versioned)
SECURITY.md           — Detailed IAM advisory (machine-parseable)
TROUBLESHOOT.md       — Failure catalog with detection and recovery procedures
```

The key properties of a stack skill are:

- **Parameterized** — every input has a validation pattern, an error message, and a recovery action [2].
- **Output-producing** — exports ARNs, IDs, and URLs for consumption by other stacks via CloudFormation exports [2][3].
- **Security-declaring** — lists exact IAM actions (no wildcards) scoped to specific resource ARNs [2][7].

These properties are deliberate design choices that serve the composition model. Parameters with validation prevent deployment failures caused by malformed inputs. Typed outputs enable explicit wiring between stacks. Security declarations at the stack level enable automated aggregation into least-privilege policies [2][7].

> **Note:** No stack skills have been implemented in the new system as of this writing. The structural templates and interaction model described here are specified and designed but not yet validated against real deployment [5].

## Pattern Skills

A pattern skill is a composition blueprint that declares which stacks to deploy, in what order, and how their outputs wire together to form a deployable full-stack solution. It does not own CloudFormation templates — it references stack skills that do [1][2][4].

The compositional nature of pattern skills is the mechanism by which the Innovation Patterns system accelerates engagements. Rather than constructing a full-stack deployment from scratch, a builder selects a pattern that encodes a proven solution architecture. The pattern provides the stack sequence, the wiring map, and the deployment order. The builder provides only the project-specific configuration [1][4].

### Anatomy of a Pattern Skill

Each pattern skill contains four files [2]:

```
SKILL.md              — Stack sequence, wiring summary, prerequisites
WIRING.md             — Detailed output-to-input mapping (machine-parseable)
ARCHITECTURE.md       — Solution description, diagram, rationale
TROUBLESHOOT.md       — Pattern-level failure catalog
```

The key properties of a pattern skill are:

- **Compositional** — references stack skills by name; does not duplicate their templates [2].
- **Order-sensitive** — the deployment sequence matters, because stacks that produce outputs must deploy before stacks that consume them [2][4].
- **Wiring-explicit** — every output-to-input connection is declared; the agent must never improvise wiring [2].
- **Architecture-aware** — includes a diagram and rationale for why these specific stacks compose into this particular solution [2].

The most notable structural difference from a stack skill is the absence of `template.yml`. Pattern skills own no CloudFormation templates. Their value lies entirely in the composition logic — which stacks, in what order, connected how [2].

### The Wiring Map

The wiring map is the defining feature that separates a pattern skill from a list of independent stacks. Without it, the stacks are disconnected CloudFormation stacks. With it, they form a coherent application with data flowing between services [1][2].

The legacy `react-rest-lambda` pattern illustrates how wiring works. This pattern composes eight stack deployments across 21 steps in three phases — backend, frontend, and authentication wiring. The wiring map declares connections such as [4]:

```
DynamoDB.TableArn      -> Lambda         dynamodb_table_arns     (parameter)
Cognito.UserPoolArn    -> API Gateway    cognito_user_pool_arn   (parameter)
Cognito.IssuerUrl      -> Lambda         env.AUTH_ISSUER         (env)
Cognito.UserPoolClientId -> Lambda       env.AUTH_AUDIENCE       (env)
Lambda.FunctionArn     -> API Gateway    lambda_function_arn     (parameter)
S3.BucketName          -> CloudFront     s3_bucket_name          (parameter)
API Gateway.ApiUrl     -> CloudFront     api_origin              (parameter)
```

Each connection specifies a source stack, a source output, a target stack, a target input, and a wiring type. The two wiring types are `parameter` (consumed at deployment time as a CloudFormation parameter) and `env` (consumed at runtime as an environment variable) [2][4].

The wiring map is non-negotiable: the agent must never improvise connections between stacks. Every output-to-input mapping is declared by the pattern author and executed mechanically by the agent [2].

### Standalone and Add-On Patterns

Patterns come in two composition types: **standalone** and **add-on** [2][4][5].

A standalone pattern deploys a complete solution from scratch. The `react-rest-lambda` pattern is a standalone pattern — it deploys all stacks needed for a React frontend backed by REST APIs, Lambda functions, DynamoDB, Cognito authentication, and CloudFront distribution [4].

An add-on pattern extends a previously deployed base pattern by adding capabilities to existing stacks and deploying new stacks alongside them. The legacy `chat` pattern illustrates this model: it assumes `react-rest-lambda` is already deployed, then adds a memory stack, rebuilds the Lambda image with new chat routes, updates existing Lambda functions with additional permissions, and wires new capabilities to existing stacks — all without redeploying the full solution [5].

Add-on patterns introduce several implications for the composition model [2][5]:

- They reference stacks they do not deploy (those stacks must already exist).
- They may modify existing stacks (for example, updating Lambda environment variables or adding IAM permissions).
- Their wiring connects new stacks to existing stacks from the base pattern.
- They must verify that prerequisite stacks exist before proceeding.

> **Open design area:** Add-on pattern composition, particularly around security metadata aggregation across base and add-on patterns, is underspecified. How the `/ipa.security` process skill aggregates IAM declarations when an add-on modifies stacks deployed by the base pattern requires further design work [2][5].

## How Stacks Compose into Patterns

The relationship between stacks and patterns is where the two types converge into a working system. This section describes the composition model that connects them [1][3].

### The Many-to-Many Relationship

The relationship between stack skills and pattern skills is many-to-many with directionality. A single stack skill can participate in multiple patterns. A pattern skill references multiple stack skills. The directionality is one-way: stacks do not know which patterns consume them; patterns know exactly which stacks they contain [1][3][5].

The following table, drawn from the legacy implementation, demonstrates real multi-pattern reuse of the same stack templates [5]:

| Stack Skill | Patterns That Use It |
|------------|---------------------|
| `dynamodb/` | react-rest-lambda, rest-lambda, sqs-lambda, s3-pipeline, chat |
| `rest-lambda/` | react-rest-lambda, rest-lambda, sqs-lambda, chat |
| `s3/` | react-rest-lambda, cloudfront-web-client, s3-pipeline, bedrock-knowledge-base |
| `cognito/` | react-rest-lambda, rest-lambda |
| `ecr/` | react-rest-lambda, rest-lambda, fullstack-streamlit |
| `api-gateway/` | react-rest-lambda, rest-lambda |
| `cloud-front/` | react-rest-lambda, cloudfront-web-client, fullstack-streamlit |
| `sqs/` | sqs-lambda, s3-pipeline |

The DynamoDB stack skill appears in at least five different patterns. The Lambda stack skill appears in at least four. This reuse is the architectural payoff of the separation: when a stack skill is updated — for example, to add encryption or change a default parameter — every pattern that references it inherits the change automatically [1][3][5].

### The Composition Pipeline

The composition pipeline describes how stack skills and pattern skills become deployed infrastructure. The pipeline moves through five stages [1][3][8]:

```
Stack Skills (metadata)
    |
    v  read by
Pattern Skill (composition blueprint)
    |
    v  read by
/ipa.compose (process skill)
    |
    v  generates
Composed Skill + Makefiles + Runbook
    |
    v  executed by
/ipa.deploy (process skill) or human (via Makefile)
    |
    v  produces
Deployed AWS Infrastructure
```

At each stage, the input is read and the output is produced by a different actor:

1. **Stack Skills** provide the raw materials — CloudFormation templates, parameters, outputs, and security metadata [2].
2. **The Pattern Skill** provides the composition logic — which stacks, in what order, with what wiring [2][4].
3. **`/ipa.compose`** reads both and generates a project-specific composed skill with concrete values (account ID, namespace, and region resolved), along with Makefiles and a runbook [1][3][8].
4. **`/ipa.deploy`** (or a human using `make`) executes the generated Makefile targets to deploy CloudFormation stacks in the declared sequence [1][8].
5. **Deployed infrastructure** is the result — running AWS resources provisioned from the stack templates, wired according to the pattern specification [1].

This pipeline is the bridge between the conceptual model (stacks and patterns as authored artifacts) and the practical workflow (the builder's compose-then-deploy sequence) [1][3].

## Why This Separation Exists

The stack/pattern split is a deliberate architectural decision that addresses specific problems observed in the legacy implementation. This section presents the design rationale — not as a suggestion, but as the reasoning behind an intentional design choice [1][3][6].

### Reuse Without Duplication

The legacy model contained twelve monolithic skill files, each up to 380 lines, where infrastructure definitions were duplicated between patterns. The DynamoDB deployment steps appeared in five or more pattern files, each with slight variations. When the DynamoDB template changed, some pattern files were updated and others were not, leading to drift [1][4][6].

The stack/pattern split eliminates this problem by extracting each service definition into a standalone stack skill. `/ipa.stack.dynamodb` exists once. Both `/ipa.pattern.react-rest-lambda` and `/ipa.pattern.sqs-lambda` reference the same stack skill. There is one definition; changes propagate automatically through every pattern that consumes it [1][3].

### Single Source of Truth for Change Propagation

Because each stack skill is defined once and referenced by name, updating a stack skill — for example, adding a new parameter, changing a default value, or strengthening a validation rule — propagates the change to every pattern that includes that stack [1][3].

In the legacy model, updating a single parameter required finding and modifying every pattern file that included the service. With the two-tier split, the update happens in one place and the composition model distributes it [1][6].

### Security Metadata at the Stack Level

Security declarations live in individual stack skills rather than at the pattern level. Each stack skill declares the exact IAM actions its resources require — scoped to specific resource ARNs, with no wildcards. The `/ipa.security` process skill reads these declarations from every stack in a composed pattern and generates aggregated least-privilege policies [1][2][7].

This design produces two significant benefits. First, adding a new stack to a pattern automatically updates the security posture — no manual IAM policy editing is required. The quality of the generated IAM policy is bounded by the precision of the security metadata in each stack skill [7]. Second, per-service scoping is preserved in the aggregated policy because each stack declares its own permissions independently [2].

The alternative — security metadata at the pattern level — would require the security process to parse different formats for each pattern and would prevent per-service IAM scoping. The current design follows the IPA Constitution's "Security First" principle: security is declared at the atomic level and composed upward, not imposed from the top down [7].

The legacy Lambda template illustrates the problem the new model solves. That template used capability flags (`EnableDynamoDB`, `EnableSQS`, `EnableBedrock`) with conditional IAM policy statements — a monolithic approach that coupled all permission logic into one template. In the new architecture, these capability-specific permissions move into each stack skill's SECURITY.md, and the security process aggregates them — replacing the monolithic conditional IAM policy with a composable declaration model [2][5][7].

### Asymmetric Deviation Risk

An error in a stack skill propagates through every pattern that references it. An error in a pattern skill affects only that pattern's execution. The blast radius is proportional to reuse [2].

This asymmetry explains why stack skills must be the most rigidly specified artifacts in the system. Every aspect — the CloudFormation template, the parameters, the outputs, the security advisory, the naming conventions — must be exact. There is one correct way to deploy a service with specific parameters, and the stack skill must describe that way precisely. Pattern skills, while mostly low freedom, allow slightly more latitude in areas such as pattern selection and error diagnosis, where heuristic judgment is appropriate [2][6].

## From Composition to Delivery

The stack/pattern distinction serves the skill library's internal architecture. At the point of customer delivery, the two-tier hierarchy dissolves. This section describes what happens at that convergence point [1][3].

### The Makefile as Convergence Point

The Makefile is where the two-tier hierarchy becomes a flat list of executable targets. The pattern provides the stack sequence and wiring; the stacks provide parameters and template paths; `/ipa.compose` generates `scripts/deploy.mk` with concrete targets that a human operator can execute without knowledge of the skill architecture [1][3][8].

This is a deliberate design virtue: the complexity that enables composability during authoring does not leak into the delivered artifact. A customer team receives Make targets such as `make deploy-dynamodb` and `make deploy-lambda`, not references to `/ipa.stack.dynamodb` or `/ipa.pattern.react-rest-lambda` [1][8].

### The Consumption Model

The stack/pattern distinction creates an asymmetric consumption model — different actors interact with different layers of the system [1][3]:

| Consumer | Stack Skills | Pattern Skills |
|----------|-------------|---------------|
| **Builder** | Never reads directly | Never reads directly |
| **`/ipa.compose`** | Reads parameters, outputs, template paths | Reads stack sequence, wiring map |
| **`/ipa.security`** | Reads Security Metadata section | Reads to identify which stacks are in the pattern |
| **`/ipa.deploy`** | Indirectly (via Makefiles) | Indirectly (via composed skill) |
| **Customer team** | Never (receives Makefile targets) | Never (receives runbook) |

The builder invokes process skills exclusively and never touches resource skills directly. The customer team receives only generated artifacts — Makefiles and runbooks. The resource library can grow with new stacks and new patterns without adding steps to the builder workflow or complexity to the customer deliverable [1][3][8].

## Naming Conventions

The IPA naming hierarchy encodes the skill taxonomy directly in the skill name [1][8]:

```
/ipa.stack.{service}         — Stack resource skill (single service)
/ipa.pattern.{architecture}  — Pattern resource skill (composition)
```

On disk, the corresponding directory paths are:

```
.claude/skills/ipa.stack.dynamodb/             — Stack skill
.claude/skills/ipa.pattern.react-rest-lambda/  — Pattern skill
```

The naming convention serves two audiences. AI agents can programmatically discover and categorize skills by parsing the prefix — `ipa.stack.*` returns all stack skills; `ipa.pattern.*` returns all pattern skills. Human authors can identify a skill's category at a glance from the name alone [1][8].

The legacy implementation used a different naming scheme — `infra/cfn/tools/` for stacks and `.kiro/skills/patterns/cfn/` for patterns — but encoded the same semantic distinction through directory structure [5].

## Sources

1. [IPA Concept Document](../../getting-started/concepts/ipa-concept.md) — Canonical definition of stacks, patterns, process/resource taxonomy, builder workflow, eject model.
2. [Authoring Resource Skills Guide](../../guides/authoring-resource-skills.md) — Stack and pattern skill templates, SECURITY.md format, WIRING.md format, quality checklist, anti-patterns.
3. [Technical Specification](../../../.context/aicode-technical.md) — System architecture, data models, inter-stack communication via CloudFormation exports, Makefile execution contract.
4. [Legacy react-rest-lambda Pattern](../../../../../../ip/innovation-patterns-legacy-mcp/.kiro/skills/patterns/cfn/react-rest-lambda.md) — 21-step full-stack deployment pattern composing 8 stacks across 3 phases.
5. [Legacy Implementation](../../../../../../ip/innovation-patterns-legacy-mcp/) — 22 stack template directories in `infra/cfn/tools/`, 12 pattern files in `.kiro/skills/patterns/cfn/`, demonstrating real-world stack reuse across patterns.
6. [Resource/Process Skill Concept Doc](../../getting-started/concepts/resource-process-skill-concept.md) — Degrees of freedom framework, security metadata interface, consumption model, naming conventions.
7. [IPA Constitution](../../../.specify/memory/constitution.md) — Security-first principle, composability principle, Makefile as single execution contract.
8. [Functional Specification](../../../.context/aicode-functional.md) — Feature inventory, business rules, stack/pattern planned implementations.
