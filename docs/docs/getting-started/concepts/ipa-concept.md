---
title: IPA Concept
sidebar_position: 2
---

# Innovation Patterns Agent Concept

The Innovation Patterns Agent (IPA) is a library of composable AI agent skills — namespaced under `/ipa.*` — that automate the deployment of full-stack infrastructure on AWS for consulting engagements [1][2]. IPA delivers three distinct categories of value: it lowers the expertise required to assemble secure cloud solutions by allowing an AI agent to compose preconfigured infrastructure patterns; it accelerates the path to production by generating human-readable deployment artifacts that customers can execute on their own terms; and it certifies security compliance through a Deliverable Security Review (DSR) that evaluates each composed pattern against per-service security standards [9].

This document establishes the high-level goals, design philosophy, and feature set of the Innovation Patterns Agent. It covers the core concepts — **patterns** (reusable, composable units of infrastructure), **stacks** (single AWS CloudFormation stacks wrapping a primary service), the **builder** (the AI agent that composes and deploys), and the **eject** workflow (the process of converting an automated deployment into standalone, human-readable artifacts). It does not cover implementation details of individual patterns, step-by-step usage instructions, or resource-level infrastructure specifications.

## The Problem IPA Solves

Consulting engagements that involve deploying infrastructure on AWS face a recurring tension between speed and control. Builders need to stand up full-stack environments quickly to demonstrate value during an **engagement** — a consulting project or client delivery. At the same time, client organizations require infrastructure that meets their security standards, follows their deployment practices, and can be maintained by their teams long after the engagement ends [2][9].

Infrastructure-as-code tools such as AWS CloudFormation and Terraform provide building blocks, but composing those blocks into a secure, production-grade **full stack** — the complete set of infrastructure layers including compute, networking, storage, security, and application — requires deep expertise across multiple AWS services. Each engagement reinvents this composition work. The result is that builders spend time on undifferentiated infrastructure plumbing rather than the innovation work that drives the engagement [2].

IPA addresses this gap by providing a library of pre-composed, security-reviewed patterns that an AI agent can deploy in minutes, with a built-in mechanism for humans to take ownership of the result [1][2].

## Three Value Drivers

IPA exists to deliver three distinct categories of value. These are not incremental improvements to existing infrastructure tooling; they represent a fundamentally different approach to how infrastructure is composed, secured, and handed off during consulting engagements [9].

### Ease of Installation and Composability

Assembling a secure, production-grade full-stack application on AWS requires expertise across networking, compute, storage, identity, and security — expertise that not every builder possesses in equal measure. A **pattern** — a reusable, composable unit of infrastructure that the agent can deploy — encodes that expertise. The builder does not need to know how to wire Amazon Cognito to Amazon API Gateway to AWS Lambda to Amazon DynamoDB; the pattern encodes that wiring knowledge [2][7].

The AI agent composes preconfigured patterns, and the builder confirms and deploys. This transforms infrastructure assembly from a high-skill manual task into a guided, AI-assisted workflow. A builder familiar with the four-step IPA workflow can deploy a full-stack application in a single session, regardless of how many AWS services are involved [7][9].

The design is deliberately opinionated. Patterns encode specific, standard configurations rather than exposing every possible option. This opinionation is a feature: it achieves the acceleration and predictability that make automation viable [3].

### Accelerated Path to Production

This is the most distinctive value IPA offers, and it requires a precise understanding of the builder-customer relationship.

Customers — the client organizations receiving the composed infrastructure — will not use IPA skills to deploy to production. They have their own deployment standards, change management processes, security reviews, and pipeline configurations. It is not possible to predict or automate these organizational standards. What IPA can do is make the manual, human-driven **path to production** — the journey from builder-composed infrastructure to organization-approved, production-grade deployment — faster, and reduce the need for cloud architect intervention [9].

IPA achieves this through two mechanisms. First, the runbook: a human-readable, step-by-step deployment document generated on every `/ipa.compose` run. A customer engineer can follow the runbook to deploy or modify the infrastructure without IPA, without the AI agent, and without the builder. Second, the Makefiles (`scripts/build.mk`, `scripts/test.mk`, `scripts/deploy.mk`): executable by humans and CI/CD pipelines alike, these are standard Make targets that any engineer can read and run [9].

The builder uses IPA to compose and deploy quickly during the engagement. The customer uses the runbook and Makefiles to reach production on their own terms. IPA is not a production tool — it is an accelerator that produces production-ready artifacts. The process by which the customer adapts the builder's output to meet their organizational standards — the **refactor** step — is entirely within their control [9].

### Security Compliance via Deliverable Security Review

Patterns are not fast at the expense of security; they are secure by default. Every pattern conforms to security standards through a Deliverable Security Review (DSR) — an AI-assisted process that evaluates the composed infrastructure against a per-service security question bank [9][10].

The DSR identifies which AWS services are present in the composed pattern, loads security questions specific to each service, and then evaluates the actual CloudFormation templates against those questions. The output is a compliance matrix — a structured report that documents which security questions passed, which require attention, and which need human review [10].

When the builder delivers a composed pattern to the customer, the DSR matrix accompanies it. The customer's security team can review the matrix rather than auditing raw CloudFormation templates. This reduces the time and expertise required for the security review phase — a phase that often blocks production deployment for weeks in large organizations [9].

## Stacks, Patterns, and Composition

The core conceptual model is a two-level abstraction. Stacks are the atomic unit; patterns compose stacks into deployable solutions [7].

### Stacks: The Atomic Unit

A **stack** is a single AWS CloudFormation stack that wraps a primary AWS service with its configuration — security settings, parameters, and outputs. Each stack translates directly to one CloudFormation stack on deployment. A Cognito User Pool stack provisions the user pool, its client, its domain, and its security settings. A DynamoDB table stack provisions the table with its billing mode, encryption, and recovery settings. An S3 bucket stack provisions the bucket with its access policies and encryption configuration [7][8].

Stacks are self-contained. Each stack declares its own parameters, provisions its resources, and exports its outputs. Critically, each stack also carries embedded security metadata — advisory information that the `/ipa.security` skill reads to generate least-privilege IAM policies for the composed pattern [11].

### Patterns: The Composition Unit

A **pattern** composes multiple stacks into a deployable solution — a full-stack application. A pattern defines three things: the deployment order of its constituent stacks, the parameter wiring between stacks, and the inter-stack dependencies [7].

For example, a pattern for a React frontend backed by a REST API on Lambda might compose stacks for DynamoDB, Amazon ECR, Lambda (buffered), Lambda (streaming), Cognito, API Gateway, S3, and CloudFront. The pattern specifies that the DynamoDB stack deploys first, the Lambda stacks deploy after ECR (because they need the container image), and the API Gateway stack deploys last (because it needs the Lambda function ARNs and the Cognito user pool ARN) [7][8].

### Inter-Stack Communication

Stacks communicate through CloudFormation output values. Each stack exports outputs — ARNs, URLs, identifiers — that dependent stacks consume as parameters [7][8].

Consider how authentication flows through a pattern. The Cognito stack exports `UserPoolArn`, `IssuerUrl`, and `UserPoolClientId`. The Lambda stack consumes `IssuerUrl` and `UserPoolClientId` as environment variables to validate JWT tokens at runtime. The API Gateway stack consumes `UserPoolArn` to configure its Cognito authorizer. The stacks themselves are decoupled — a stack does not need to know which other stacks consume its outputs, only what it exports. The pattern definition is where the wiring between stacks is specified [7][8].

## The Skill Set: Process Skills and Resource Skills

IPA skills fall into two categories: process skills that orchestrate the workflow, and resource skills that define deployable infrastructure [11].

### Process Skills

Process skills are verbs — they drive the lifecycle but do not themselves define infrastructure. There are five process skills [11]:

| Skill | Purpose |
|-------|---------|
| `/ipa.init` | Establish project defaults: AWS profile, IAM role ARNs, platform selection |
| `/ipa.security` | Initialize or update the security posture for the composed pattern |
| `/ipa.compose` | Select a pattern and generate the default skill, Makefiles, and runbook |
| `/ipa.deploy` | Build and deploy the composed pattern via Makefiles |
| `/ipa.codepipeline` | Set up a CI/CD pipeline that executes the same Makefiles |

Each process skill does one thing. The builder memorizes a short sequence — not a complex decision tree. `/ipa.security` automatically determines whether it needs to initialize security (first run) or update it (subsequent runs); the builder does not choose between separate init and update commands [11].

### Resource Skills

Resource skills are nouns — they define what gets deployed. They are organized at two levels [11]:

**Stack skills** (`/ipa.stack.*`) define a single CloudFormation stack wrapping a primary service. Examples include `/ipa.stack.cognito`, `/ipa.stack.dynamodb`, `/ipa.stack.lambda`, and `/ipa.stack.s3`. Each stack skill encapsulates the CloudFormation template path, parameters, expected outputs, and security metadata [11].

**Pattern skills** (`/ipa.pattern.*`) compose multiple stack skills into a deployable solution. Examples include `/ipa.pattern.react-rest-lambda` and `/ipa.pattern.sqs-lambda`. A pattern skill defines the deployment order, parameter wiring between stacks, and the solution architecture [11].

When `/ipa.compose` runs, it selects a pattern from the available resource skill library and writes a concrete, project-specific pattern skill to `.claude/skills/`. This generated skill contains the specific stack sequence, parameter values, naming conventions, and output wiring for the project. The AI agent reads it and follows it [7].

## The Builder Workflow

The builder workflow uses only process skills, executed in sequence [7][11]:

```
/ipa.init         →  Establish project defaults
/ipa.security     →  Provision or update IAM roles
/ipa.compose      →  Select a pattern; generate skill, Makefiles, and runbook
/ipa.deploy       →  Build and deploy the composed pattern
/ipa.codepipeline →  (Optional) Set up CI/CD pipeline
```

The core path is four steps: init, security, compose, deploy. `/ipa.deploy` always runs `scripts/build.mk` and `scripts/deploy.mk` — it does not need to know which pattern was composed or which stacks are being deployed. The Makefiles encode that knowledge [7].

All skills are idempotent — running them multiple times does not destroy existing configuration [2]. When the pattern evolves, the builder re-runs `/ipa.compose` (which regenerates the Makefiles and runbook), then `/ipa.security` (which recalculates least-privilege permissions from updated stack metadata), then `/ipa.deploy`. The same four-step sequence, repeatable and safe [11].

### Self-Diagnosing and Self-Healing

The IPA is designed to detect and recover from problems without requiring the builder to manually troubleshoot [11].

The agent can detect deployment failures — stack rollbacks, timeout errors, permission denials — and identify the root cause. It can recognize configuration drift between the composed pattern and the actual deployed state. It can verify that the security posture matches the expected least-privilege policy. When it identifies a problem, it can take corrective action: retry a failed deployment after correcting the issue, re-run `/ipa.security` if permission errors indicate the security posture is out of date, or update the Makefiles and runbook if the pattern has changed since the last compose [11].

This behavior is enabled by the agent-native design. Because the AI agent is the primary operator, it can read error messages, analyze CloudFormation events, compare expected and actual state, and take corrective action — all within the same workflow, without switching tools or requiring human intervention. The builder's role shifts from "debug the deployment" to "confirm the agent's proposed fix" [11].

## The Eject Workflow and Path to Production

Every time `/ipa.compose` runs, it produces three categories of output [9]:

1. A **pattern skill** in `.claude/skills/` — AI-readable, used by the builder during the engagement. This is not delivered to the customer.
2. **Makefiles** at `scripts/build.mk`, `scripts/test.mk`, and `scripts/deploy.mk` — executable by humans and CI/CD pipelines. These are delivered to the customer.
3. A **runbook** at `docs/infra/runbook.md` — a human-readable, step-by-step document. This is the primary customer-facing deliverable.

### The Runbook

The runbook is a human-executable deployment document that explains every stack, every parameter, every output, and every dependency in the composed pattern. A customer engineer can follow it to deploy or modify the infrastructure without IPA, without the AI agent, and without the builder [9].

The runbook is generated fresh on every compose run — not as an afterthought, but as a first-class output of the composition process. If the pattern changes, the runbook changes with it. This is the **eject** mechanism: the process of converting an automated deployment into a standalone, human-readable project that can be maintained independently [9].

### The Makefiles

The Makefiles at `scripts/build.mk`, `scripts/test.mk`, and `scripts/deploy.mk` are standard Make targets that any engineer can read and run [7]. They are executable by the builder locally, by the AI agent during `/ipa.deploy`, and by a CI/CD pipeline when `/ipa.codepipeline` configures AWS CodePipeline. The same Makefiles the builder used during the engagement are the same ones the customer can execute in production [9].

This universal execution contract means there is one way to build, one way to test, and one way to deploy — regardless of whether the trigger is a human, an AI agent, or a pipeline [7].

### From Builder to Customer

The handoff lifecycle proceeds as follows: the builder composes a pattern and deploys it during the engagement. The customer receives the runbook and Makefiles. The customer's team reads the runbook, understands the infrastructure, and adapts it to their organizational standards — naming conventions, network configurations, compliance requirements, pipeline tooling. The customer then deploys to production through their own processes [9].

The customer's adaptation of the builder's output to their organizational standards — the **refactor** step — is where IPA's contribution ends. IPA does not attempt to automate the last mile. Organizational production standards are too varied and too rigorous to predict. Instead, IPA makes the manual path faster by providing clear documentation (the runbook) and an executable starting point (the Makefiles). The customer's team requires less cloud architect intervention because the runbook explains the reasoning behind each infrastructure decision, not just the steps to execute [9].

## Security Model

Security in IPA is a precondition, not a phase. The project's first design tenet states: "All generated infrastructure and code follows AWS security best practices" [1]. This commitment is enforced through a unified security skill, metadata-driven least privilege, and the Deliverable Security Review.

### Unified Security Skill

A single process skill — `/ipa.security` — manages the entire security lifecycle [11]. It automatically determines whether security needs to be initialized (first run, when no IAM roles exist) or updated (subsequent runs, when the pattern has changed). The builder does not choose between separate initialization and update commands; the skill detects the current state and acts accordingly [11].

`/ipa.security` generates least-privilege IAM policies by reading security metadata embedded in each stack skill used by the composed pattern. Each resource skill carries advisory information describing the permissions its stack requires. For example, a DynamoDB stack skill advises that it requires `dynamodb:PutItem`, `dynamodb:GetItem`, and `dynamodb:Query` on the table ARN. An S3 stack skill advises that it requires `s3:PutObject` and `s3:GetObject` on the bucket ARN, with public access denied. `/ipa.security` composes these individual advisories into a coherent security posture: a Builder Execution Role for local deployments, a CodeBuild Execution Role for pipeline deployments, and per-function execution roles — all scoped to exactly the permissions the pattern requires [11].

As the pattern evolves — stacks added or removed via `/ipa.compose` — re-running `/ipa.security` automatically recalculates permissions, reducing the blast radius over time [11].

### Deliverable Security Review

The Deliverable Security Review is an AI-assisted evaluation that certifies the composed pattern against security standards [9][10].

The DSR process has four phases. Service discovery identifies which AWS services are present in the composed pattern by scanning the CloudFormation templates. Question loading retrieves a set of security questions specific to each identified service — for example, questions about S3 bucket policies, Lambda execution roles, or Cognito authentication settings. Code interrogation evaluates each question against the actual infrastructure code: is the S3 bucket public? Does the Lambda function have least-privilege permissions? Is encryption at rest enabled? The output is a compliance matrix — a structured report documenting which security questions passed, which failed, and which require human review [10].

The DSR matrix accompanies the delivered infrastructure. The customer's security team reviews the matrix rather than auditing raw CloudFormation templates, reducing the time and expertise required for the security review phase of the path to production [9].

## Design Tenets

Five tenets govern all design decisions in the Innovation Patterns Agent [1]:

| Tenet | Commitment |
|-------|------------|
| **Security First** | All generated infrastructure and code follows AWS security best practices. Security is a precondition, not a bolt-on. |
| **Composability** | Infrastructure components are modular and reusable. Stacks compose into patterns; patterns compose into solutions. |
| **Human Control** | The eject capability ensures that humans can always take over from the agent. The runbook and Makefiles are always available. |
| **Pattern Reusability** | Patterns are designed to be referenced and extended across engagements, not rebuilt each time. |
| **Agent-Native** | Skills are designed for AI agents as the primary consumers, with human-readable outputs as generated artifacts. |

The Agent-Native tenet is the most distinctive. IPA inverts the typical developer-tool relationship: the AI agent is the primary operator, and human-readable artifacts — runbooks, inline comments, documentation — are generated outputs, not the primary interface. The agent reads skill files and Makefiles natively; the runbook is produced for the humans who will eventually take ownership [1].

These tenets are design commitments, not aspirations. They constrain every decision — from the choice of CloudFormation as the primary IaC tool (Security First) to the requirement that every compose run generates a runbook (Human Control) [1][6].

## What Comes Next

This document establishes the conceptual foundation of the Innovation Patterns Agent. The concepts introduced here — stacks, patterns, process skills, resource skills, the eject workflow, the DSR, and the builder-to-customer handoff — are the vocabulary for the detailed documentation that follows.

Per-pattern reference documentation will describe the specific stacks and wiring for each supported pattern. Usage guides will provide step-by-step instructions for the builder workflow. Infrastructure architecture documents will specify resource-level configurations. Each of these documents builds on the concepts defined here.

The measure of success for IPA is the three value drivers: whether it makes cloud infrastructure easier to assemble, whether it accelerates the customer's path to production, and whether it delivers infrastructure that passes security review before the customer's team ever sees it [9].

## References

1. IPA Agent Skills Spec — functional and non-functional requirements, design tenets, affected areas; states "CloudFormation Primary" as the IaC strategy
2. System description — skill descriptions, architecture, composition model, eject workflow, security model
3. Project Brief (`.context/aidocs.md`) — project-level objectives, audience, constraints, key terms
4. Codebase exploration — file inventory, CI/CD configuration, infrastructure module state
5. Architecture description — `scripts/` and `infra/` directory separation, isolation model, IaC tool organization
6. IaC tool strategy — rationale for CloudFormation-first, Terraform-second, CDK-deferred approach; AI composability argument
7. Stack-pattern conceptual model — stack-pattern hierarchy, skill-based composition, Makefile-driven build and deploy, workflow requirements
8. Legacy IPA codebase — pattern files, stack templates, deployment scripts; used as inspiration for the current design
9. Value proposition — three value drivers, builder-customer relationship, runbook as primary deliverable, Makefile execution model
10. Legacy DSR implementation — Deliverable Security Review architecture, per-service question banks, compliance matrix output
11. Skill taxonomy and security model — process skills versus resource skills, unified `/ipa.security`, metadata-driven least privilege, self-diagnosing and self-healing
