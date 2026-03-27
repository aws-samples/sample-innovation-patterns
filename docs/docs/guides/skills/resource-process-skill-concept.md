---
title: Resource Skills vs. Process Skills
sidebar_position: 1
---

# Resource Skills vs. Process Skills

The Innovation Patterns Agent (IPA) organizes its skill library around a single architectural distinction: resource skills define *what* gets deployed, and process skills orchestrate *how* it gets deployed. This is not a naming convention. It is a separation of concerns that governs how skills are categorized, structured, consumed, and extended within the framework [1] [3] [4].

Resource skills are infrastructure nouns — a DynamoDB table, a Cognito user pool, a full-stack pattern (a reusable, composable unit of infrastructure that the builder, the automation agent, can deploy). Process skills are workflow verbs — initializing a project, provisioning security, composing a pattern, deploying stacks. The builder interacts exclusively with process skills. Process skills, in turn, read resource skill metadata to do their work. This asymmetry is deliberate: it keeps the builder workflow simple while allowing the resource library to grow without adding complexity to the workflow [1] [5] [8].

This document defines both categories, describes their structural anatomy, formalizes the naming conventions and categorization criteria, and explains how the two types interact through the security metadata interface and the Makefile generation pipeline. It does not cover implementation details of individual skills, deployment procedures, or the full IPA skill inventory — only representative examples are used to illustrate each category.

## The Core Distinction: Infrastructure Nouns and Workflow Verbs

The IPA concept document establishes the fundamental taxonomy: "IPA skills fall into two categories: process skills that orchestrate the workflow, and resource skills that define deployable infrastructure" [1]. This distinction determines three things about every skill in the library: who reads it (the builder or the agent), how it is structured (procedural workflow or declarative metadata), and how it participates in the system (direct invocation or library consumption) [1] [3].

The two categories are not symmetric. Process skills are few in number and form a fixed workflow sequence. Resource skills are numerous and form a growing library. The builder (the automation agent that composes and deploys patterns into a working stack) invokes process skills directly and never touches resource skills. This asymmetry is a deliberate design choice that isolates the builder from the complexity of the infrastructure library [1] [8].

### Resource Skills: What Gets Deployed

A resource skill is a declarative, non-interactive metadata description of deployable infrastructure. Resource skills do not execute — they describe what exists in AWS after deployment. They are consumed by process skills, never invoked directly by the builder [1] [3].

Resource skills divide into two tiers with distinct structural templates [1] [3] [7]:

| Tier | Description | Naming Convention | Examples |
|------|-------------|-------------------|----------|
| **Stack skills** | Atomic units wrapping a single AWS service | `/ipa.stack.{service}` | `/ipa.stack.dynamodb`, `/ipa.stack.cognito`, `/ipa.stack.lambda` |
| **Pattern skills** | Compositions of stacks into deployable solutions (full-stack architectures spanning compute, networking, storage, security, and application layers) | `/ipa.pattern.{architecture}` | `/ipa.pattern.react-rest-lambda`, `/ipa.pattern.sqs-lambda` |

Stack skills declare parameters, outputs, and security metadata for a single AWS service. Pattern skills declare deployment order and inter-stack wiring for a complete architecture. These are structurally different skill types that share the "resource" category because both define infrastructure rather than orchestrate workflows [1] [3] [7].

### Process Skills: How It Gets Deployed

A process skill is a stateful, interactive workflow step that reads resource skill metadata and executes actions against AWS. Process skills are the builder's sole interface to the IPA system [1] [5] [8].

The five process skills form a linear workflow sequence [1] [8]:

| Process Skill | Verb | Action |
|---------------|------|--------|
| `/ipa.init` | Initialize | Establish project defaults (namespace, region, environment) |
| `/ipa.security` | Secure | Provision or update least-privilege IAM roles |
| `/ipa.compose` | Compose | Select a pattern, generate deployment artifacts |
| `/ipa.deploy` | Deploy | Build and deploy the composed pattern |
| `/ipa.codepipeline` | Automate | Set up a CI/CD pipeline for continuous deployment |

Each process skill performs a specific action in the deployment lifecycle. The builder invokes them in sequence — init, then security, then compose, then deploy — and each skill reads the state produced by the previous one [1] [8]. Process skills present confirmation gates before writing state, include error handling with cataloged failure modes, and verify their own output before completing [5] [9].

## Why the Distinction Exists

The resource/process split is a deliberate architectural decision that addresses three specific design problems observed in the legacy IPA implementation and the current architecture requirements [6] [7].

### Composition Over Monoliths

The legacy IPA implementation contained 12 monolithic skill files that mixed infrastructure definitions with deployment procedures [6] [7]. A single skill file such as `react-rest-lambda.md` contained DynamoDB table definitions, Lambda function configurations, API Gateway settings, deployment sequences, and error handling — all interleaved. To reuse the DynamoDB definition in a different pattern, an author had to copy the relevant sections and adapt them, creating maintenance burden and drift risk [6] [7].

The resource/process split solves this by extracting each AWS service definition into a standalone stack resource skill. `/ipa.stack.dynamodb` exists once in the library. Both `/ipa.pattern.react-rest-lambda` and `/ipa.pattern.sqs-lambda` reference the same stack skill. One definition serves multiple compositions. This composability is how patterns (reusable, composable units of infrastructure) accelerate engagements (consulting projects or client deliveries where patterns accelerate infrastructure setup) — standard infrastructure components compose into different architectures without duplication [1] [6] [7].

### Single Source of Truth for Change Propagation

In the legacy model, modifying a CloudFormation parameter for DynamoDB required finding and updating every pattern file that included DynamoDB. With the split model, the stack skill is the single source of truth for that service. Process skills (`/ipa.compose`, `/ipa.deploy`) read the current stack skill metadata at execution time, so changes to a stack skill propagate automatically through every pattern that references it [3] [7].

### Security Metadata Requires a Clear Owner

The `/ipa.security` process skill generates least-privilege IAM policies by composing permission advisories from individual stack skills [1] [5]. If security metadata were embedded in pattern-level monolithic files, the security skill would need to parse different file formats for each pattern. With the split model, every stack skill has a standardized Security Metadata section. The security process skill reads the same structured format regardless of which pattern is being composed [5] [7]. The security metadata interface is detailed in a dedicated section below.

## Structural Anatomy of Each Skill Type

The two categories produce structurally different skill files. The differences are not cosmetic — they reflect the fundamentally different roles each category plays in the system [3] [5] [7].

### Process Skill Structure

The two implemented process skills (`ipa.init` at 719 lines and `ipa.security` at 717 lines) demonstrate a consistent structural template [5] [9]:

```
Front matter: name, description, model
Main heading: action verb + scope
├── Pre-execution checks (detect current state)
├── Interactive prompt sequence (collect input)
├── Validation tables (regex patterns, error messages)
├── State-dependent branching (first run vs. re-run)
├── Confirmation gate (summary table, explicit approval)
├── Execution steps (numbered, sequential)
├── Post-execution verification
├── Error handling (cataloged failure modes with recovery)
└── Completion report (what was done, what to do next)
```

Process skills are state-aware: they detect existing project state before acting and branch their behavior accordingly (for example, distinguishing a first run from a re-run). They are interactive: they collect input from the builder through prompt sequences with validation. They are transactional: they read state, transform it, and write new state, with confirmation gates before any write operation [5] [9].

The error handling in process skills is not generic. Each skill catalogs its specific failure modes (for example, CloudFormation stack creation failure, insufficient IAM permissions, missing `.env` configuration) and provides recovery instructions for each [5].

### Stack Resource Skill Structure

The technical specification and resource-skill-guidance research define the following structural template for stack resource skills [3] [7]:

```
Front matter: name, description
Main heading: service name
├── Parameters table (name, type, default, validation)
├── Outputs table (name, export convention, description)
├── Security Metadata (IAM actions, resource scope, controls)
├── Template reference (path to CloudFormation YAML)
└── Dependencies (what must exist before this stack)
```

Stack resource skills are declarative: they describe what exists, not how to create it. They are non-interactive: they contain no prompt sequences, no confirmation gates, and no error handling. They are metadata-focused: their primary purpose is to provide structured information that process skills consume [3] [7].

**Note:** As of this writing, no stack resource skills have been implemented. The structure described above is derived from the technical specification [3] and the resource-skill-guidance research [7]. It has not been validated against real deployment.

### Pattern Resource Skill Structure

Pattern resource skills use a different structural template that reflects their composition-focused role [1] [3] [7]:

```
Front matter: name, description
Main heading: architecture name
├── Architecture diagram (visual composition)
├── Stack sequence (ordered deployment list)
├── Parameter wiring table (source output → target parameter)
├── Environment variables (runtime configuration contract)
└── Composition points (standalone vs. add-on, prerequisites)
```

Pattern resource skills declare inter-stack relationships: which stacks deploy in what order, how outputs from one stack become parameters for the next, and what environment variables the composed application requires. The `/ipa.compose` process skill reads this metadata to generate Makefiles and the project-specific deployment runbook [1] [3] [7].

Like stack skills, pattern resource skills have not been implemented yet. The structure is specified but not proven in practice [7].

## The Consumption Model: Who Reads What

The resource/process distinction creates an asymmetric consumption model. Different consumers interact with each skill type in different ways [1] [3]:

| Consumer | Process Skills | Stack Resource Skills | Pattern Resource Skills |
|----------|---------------|----------------------|------------------------|
| **Builder** | Invokes directly (the only skills the builder touches) | Never sees directly | Never sees directly |
| **`/ipa.compose`** | N/A (is a process skill) | Reads parameters, outputs, template paths | Reads stack sequence, wiring map |
| **`/ipa.security`** | N/A (is a process skill) | Reads Security Metadata section | Reads to identify which stacks are in the pattern |
| **`/ipa.deploy`** | N/A (is a process skill) | Indirectly (via generated Makefiles) | Indirectly (via generated composed skill) |
| **Runbook** | N/A | Indirectly (metadata feeds runbook generation) | Indirectly (architecture description feeds runbook) |

### Builder Workflow: Process Skills as the Interface

The builder follows a four-step workflow: init, security, compose, deploy [1] [8]. At no point does the builder read or invoke a resource skill. The process skills insulate the builder from the resource library entirely. This means the resource library can grow — new stack skills, new pattern skills — without adding any steps to the builder workflow. The builder's experience remains the same four commands regardless of how many resources the library contains [1] [8].

### Agent Workflow: Resource Skills as the Library

Process skills are the primary consumers of resource skills. When `/ipa.compose` runs, it reads the selected pattern resource skill to determine which stacks to include and how to wire them together, then reads each referenced stack resource skill for parameters, outputs, template paths, and security metadata [1] [3]. When `/ipa.security` runs, it reads the Security Metadata section from every stack skill in the composed pattern to generate least-privilege IAM policies [5]. The agent, not the builder, navigates the resource library.

## Naming Conventions and Categorization Criteria

The IPA naming hierarchy encodes categorization directly in the skill name. The category is visible at a glance [1] [4] [8].

### Namespace Hierarchy

The IPA constitution defines the naming convention for skill files [8]:

```
/ipa.{verb}                  → Process skill
/ipa.stack.{service}         → Stack resource skill
/ipa.pattern.{architecture}  → Pattern resource skill
```

Skill files follow the path convention `.claude/skills/ipa.{type}.{name}.md` [8]. The `type` segment serves as the category marker. For process skills, the type is the verb itself (`init`, `security`, `compose`, `deploy`, `codepipeline`). For resource skills, the type is the tier (`stack` or `pattern`) followed by the specific service or architecture name.

### Decision Rules for New Skills

When a new skill is proposed for the IPA library, the following decision rules determine its category [1] [5]:

1. **Does it define deployable infrastructure?** If the skill describes a thing that exists in AWS after execution — a DynamoDB table, a Lambda function, a full-stack architecture — it is a resource skill.

2. **Does it orchestrate a workflow step?** If the skill performs an action that reads, transforms, or acts upon other skills' metadata — initializing a project, computing security policies, generating Makefiles, running deployments — it is a process skill.

3. **Does the builder invoke it directly?** If yes, it is a process skill. Resource skills are library items consumed by process skills, never invoked by the builder [1].

4. **Edge case: what if a skill does both?** Apply the primary purpose test (see below).

### Edge Cases

`/ipa.security` is the clearest edge case in the current library. It reads metadata from stack resource skills (a consumption action) and deploys IAM CloudFormation stacks (an infrastructure action). It is categorized as a process skill because its primary purpose is to orchestrate the security workflow — the IAM stacks are a means of fulfilling that workflow, not the skill's declarative identity [1] [5].

The primary purpose test asks: "Is the skill's primary purpose to define infrastructure, or to orchestrate a workflow?" For `/ipa.security`, the answer is unambiguous — the IAM stacks are always a product of the workflow, never an end in themselves. The skill's output changes whenever the composed pattern changes, because different patterns require different IAM policies [5].

As the skill library grows, additional edge cases are likely to emerge. A hypothetical `/ipa.validate` skill that checks deployed state against resource skill metadata would raise similar questions. The decision rules above provide a first-pass framework for resolving such cases, though the framework may require refinement as the library matures.

## The Security Metadata Interface

Security metadata in stack resource skills is the most consequential interface between the two categories. It is where resource skills declare what they need, and process skills enforce what they get [1] [5] [7].

Each stack resource skill includes a Security Metadata section listing the IAM permissions its resources require. The technical specification defines the following format [3]:

```markdown
## Security Metadata
- **Required Permissions**: `dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:Query`
- **Resource Scope**: Table ARN (`arn:aws:dynamodb:{region}:{account}:table/{TableName}`)
- **Encryption**: Server-side encryption enabled by default
- **Access Pattern**: No public access; IAM-only authentication
```

The `/ipa.security` process skill consumes this metadata through a five-step sequence [5]:

1. Identify which stacks are in the composed pattern
2. Read the Security Metadata section from each stack skill
3. Aggregate permissions across all stacks
4. Generate least-privilege IAM policy documents
5. Deploy IAM roles via CloudFormation

This interface establishes resource skills as the **source of truth** for security requirements and the security process skill as the **enforcement mechanism**. The quality of the generated IAM policy is bounded by the precision of the security metadata in each stack skill. Specific advisories — such as `dynamodb:PutItem` scoped to a table ARN — produce tight policies. Vague advisories produce vague policies [7].

The resource-skill-guidance research proposes a structured YAML format to make security advisories machine-parseable [7]:

```yaml
security:
  permissions:
    - actions: [dynamodb:PutItem, dynamodb:GetItem, dynamodb:Query]
      resource: "!Output TableArn"
      purpose: "CRUD operations on the application table"
  controls:
    - type: encryption_at_rest
      enabled: true
```

This structured format enables the security process skill to aggregate permissions programmatically rather than parsing free-text advisories. The format is proposed but not yet implemented [7].

## Degrees of Freedom and Authoring Guidance

The Anthropic skill authoring best practices introduce a "degrees of freedom" framework that applies differently to each category [2] [6] [7]:

| Freedom Level | When to Use | Process Skill Examples | Resource Skill Examples |
|---------------|-------------|------------------------|------------------------|
| **High** | Multiple valid approaches | Choosing which pattern to compose | None — resource skills do not offer choices |
| **Medium** | Preferred approach exists, some variation acceptable | Configuring security group rules based on project needs | None |
| **Low** | One safe path; deviation causes failures | CloudFormation deploy commands, IAM policy creation | All aspects: templates, parameters, wiring, naming |

Resource skills should be authored with **uniformly low degrees of freedom** [7]. The CloudFormation template is exact. The parameters have validation rules. The outputs follow fixed export conventions. The security advisory lists specific IAM actions scoped to specific resources. There is no "customize as needed" in a resource skill — the precision of the metadata is what makes composition safe.

Process skills operate at **low-to-medium freedom** [6]. Most steps, particularly AWS CLI commands and CloudFormation operations, are low freedom. These steps follow a narrow, exact path where deviation causes infrastructure failure. However, some steps — such as pattern selection during `/ipa.compose` or error diagnosis during `/ipa.deploy` — involve heuristic judgment where medium freedom is appropriate [6].

The deviation risk between the two categories is asymmetric. An error in a resource skill propagates through every pattern that references it, because multiple process skills consume the same resource skill metadata. An error in a process skill affects only its own execution [7]. This asymmetry reinforces the need for low degrees of freedom in resource skills — the blast radius of a resource skill error is proportional to its reuse.

## The Generated Composed Skill

When `/ipa.compose` runs, it reads resource skills (both the selected pattern and its referenced stacks) and generates a project-specific skill file in `.claude/skills/` [1] [3]. This generated artifact occupies an ambiguous position in the resource/process taxonomy.

The composed skill looks like a resource skill — it declares stack sequences, parameter values, and wiring maps. It behaves like a resource skill — `/ipa.deploy` reads it for deployment instructions. However, it is project-bound: it contains concrete values (account ID, namespace, region) rather than reusable abstractions. And it is generated, not authored: it is a transient output of the compose process, not a library entry [1] [3].

The IPA concept document treats it as a generated artifact: "When `/ipa.compose` runs, it selects a pattern from the available resource skill library and writes a concrete, project-specific pattern skill to `.claude/skills/`" [1]. For the purposes of the resource/process taxonomy, the composed skill is a **derivation** of resource skills — it inherits the structural format of a pattern resource skill but is not a member of the reusable library. It is an output of the compose process, not a skill to be categorized.

## Convergence: The Makefile as Handoff Artifact

The Makefile is where the two categories converge into a single executable artifact [1] [3] [8]:

```
Resource skills (metadata) → /ipa.compose (process skill) → Makefile (generated artifact)
```

The pattern resource skill provides the stack sequence and wiring map. The stack resource skills provide the parameters, template paths, and naming conventions. The `/ipa.compose` process skill reads all of this and generates `scripts/deploy.mk` with concrete Make targets — one per stack, in dependency order, with parameter values resolved from `.env` variables [3].

The IPA constitution establishes the Makefile as the single execution contract: "The Makefiles (`scripts/*.mk`) are the single source of truth for build, test, and deploy. The AI agent, human builders, and CI/CD pipelines MUST all execute the same targets" [8]. This means the Makefile is the handoff artifact — the point where the agent-native resource/process architecture produces a human-executable output.

After the eject workflow (the process of converting an automated deployment into a standalone, human-readable project), the resource/process distinction is invisible to the recipient. The customer's team sees only the Makefile and the runbook. The noun/verb split is an authoring concern — it serves the skill library's internal architecture — and dissolves into a flat list of Make targets at the point of delivery. This is a design virtue: the complexity that enables composability and reuse during authoring does not leak into the delivered artifact [1] [3] [8].

## Extending the Framework

The resource/process distinction provides a decision framework for every new skill added to the IPA library. Each extension scenario affects only one side of the divide, keeping changes localized and reducing the risk of cross-cutting regressions [1] [3].

### Adding a New AWS Service

To add support for a new AWS service (for example, Amazon SQS), the author creates a stack resource skill (`/ipa.stack.sqs`) with parameters, outputs, security metadata, and a CloudFormation template. No process skills require modification — `/ipa.compose` and `/ipa.security` already know how to read stack skill metadata in the standard format. The resource library grows; the builder workflow remains the same [1] [3].

### Adding a New Composition Pattern

To add a new architecture (for example, an event-driven pattern), the author creates a pattern resource skill (`/ipa.pattern.sqs-lambda`) that references existing stack skills with a new wiring map. Again, no process skills require modification. The pattern library grows; the four-step builder workflow remains the same [1].

### Adding a New Workflow Capability

To add a new workflow step (for example, teardown), the author creates a process skill (`/ipa.teardown`) that reads the composed pattern and executes stack deletions in reverse order. No resource skills require modification. The workflow extends; the resource library remains the same.

This extensibility is the architectural payoff of the resource/process split. New AWS services expand the resource library without touching the workflow. New architectures compose existing resources without touching the workflow. New workflow capabilities extend the process layer without touching the resource library. Each new capability is localized to its category [1] [3].

## Conclusion

The resource/process distinction is the primary organizing principle of the IPA skill library. It separates infrastructure definitions (resource skills) from workflow orchestration (process skills), enabling composability, reuse, and independent evolution of each category.

The practical consequence is a system where the resource library can grow — new AWS services, new architecture patterns — without adding complexity to the builder workflow. Conversely, the workflow can gain new capabilities — teardown, validation, pipeline setup — without modifying the resource library. The security metadata interface ensures that each resource skill declares its own IAM requirements, and the security process skill enforces least-privilege policies across any composition of those resources [1] [3] [5] [7].

The framework is in early implementation. Two process skills (`ipa.init` and `ipa.security`) are operational and validate the process skill structural template. Resource skills (both stack and pattern tiers) are specified but not yet implemented. As the library grows and resource skills are built, the categorization criteria and structural templates described in this document will be tested against real deployment — and refined as edge cases emerge [5] [7].

## Sources

1. **IPA Concept Document** (`docs/concepts/ipa-concept.md`) — Canonical definition of process vs. resource skills, stacks and patterns, the builder workflow, security model, eject workflow, and design tenets.
2. **Anthropic Skill Authoring Best Practices** (`https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices`) — Official guidance on degrees of freedom, progressive disclosure, conciseness, and feedback loops.
3. **Technical Specification** (`.context/aicode-technical.md`) — System architecture, component diagram, data models, CloudFormation structure, stack naming, Makefile execution contract, and inter-stack data flow.
4. **Functional Specification** (`.context/aicode-functional.md`) — Feature inventory organized by process/resource categories, business rules, and glossary definitions.
5. **ipa.init and ipa.security Skill Files** (`.claude/skills/ipa.init/SKILL.md`, `.claude/skills/ipa.security/SKILL.md`) — Two implemented process skills demonstrating validation tables, state detection, confirmation gates, CloudFormation deployment, and error handling patterns.
6. **Process Skill Guidance Research** (`docs/working/concepts/process-skill-guidance/research.md`) — Structural patterns from the speckit suite and Anthropic guidance applied to IPA process skills; degrees of freedom framework.
7. **Resource Skill Guidance Research** (`docs/working/concepts/resource-skill-guidance/research.md`) — Two-tier taxonomy, declarative metadata as primary interface, security advisory design, inter-stack wiring safety, and naming conventions.
8. **IPA Constitution** (`.specify/memory/constitution.md`) — Seven core principles, naming conventions, builder workflow sequence, and Makefile as single execution contract.
9. **IPA Agent Skills Spec** (`docs/working/specs/ipa-agent-skills/README.md`) — Original requirements and five design tenets (security first, composability, human control, pattern reusability, agent-native).
10. **Code Context** (`.context/aicode.md`) — Key terms defining process skill and resource skill, architecture overview, patterns, and constraints.
