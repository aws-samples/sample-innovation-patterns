---
title: IPA Concept
sidebar_position: 2
---

# Innovation Patterns Agent Concept

The Innovation Patterns Agent (IPA) is a library of composable AI agent skills — namespaced under `/ipa-*` — that automate the deployment of full-stack infrastructure on AWS [1]. Each skill is a Markdown instruction document in `.claude/skills/` that Claude Code interprets and executes. IPA follows an agent-native design: the AI agent is the primary operator, and human-readable outputs — Makefiles, CloudFormation templates, and security registers — are generated artifacts for the humans who take ownership of the deployed infrastructure [1].

This document covers what IPA is, why it exists, and the core concepts that the rest of the documentation builds on. It does not cover installation, individual skill references, or deployment procedures.

## The Problem IPA Solves

Consulting engagements that deploy infrastructure on AWS face a recurring tension between speed and control. The builder — the consultant operating IPA — needs to stand up full-stack environments quickly to demonstrate value during an engagement. At the same time, the customer — the client organization receiving the infrastructure — requires output that meets their security standards, follows their deployment practices, and can be maintained by their teams independently [1].

Infrastructure-as-code tools such as AWS CloudFormation provide building blocks, but composing those blocks into a secure, full-stack application requires deep expertise across multiple AWS services. Each engagement reinvents this composition work. Builders spend time on undifferentiated infrastructure plumbing rather than the innovation work that drives the engagement [1].

IPA addresses this gap by encoding multi-service infrastructure expertise into composable stacks that an AI agent assembles and deploys in minutes. The output is evolvable POC infrastructure — structured for customer teams to adapt and harden, not to deploy as-is to production [1].

## Core Concepts

IPA has a small vocabulary — skills, stacks, tiers, and composition — that the rest of the documentation builds on.

### Skills

Skills fall into three categories [2].

**Process skills** are workflow verbs. They drive the IPA lifecycle but do not themselves define infrastructure. The core lifecycle is four steps: `/ipa-init` → `/ipa-compose` → `/ipa-prepare` → `/ipa-deploy`. Additional process skills include `/ipa-destroy` (teardown), `/ipa-help` (state inspection), and `/ipa-codepipeline` (CI/CD). `/ipa-security` is a backing skill invoked by `/ipa-compose` for initial provisioning [2].

**Stack skills** (`/ipa.stack.*`) are infrastructure nouns. Each stack skill wraps a CloudFormation template with skill metadata — a `SKILL.md` describing the stack's parameters, outputs, and wiring contract, and a `SECURITY.md` documenting its security posture [2][4].

**Authoring skills** are meta-skills that create and update stack skills. The `/ipa-author-stack` skill handles the full range, from single-service stacks to multi-service tiers [2].

All skills are idempotent. Running a skill multiple times does not destroy existing configuration or infrastructure [1].

### Stacks and Tiers

A **stack** is the atomic deployment unit — a single CloudFormation stack. Stacks have one of two lifecycle classifications. Prepare stacks are one-time prerequisites — Cognito user pools, ECR repositories — that persist across teardown and redeployment cycles. Deploy stacks are application infrastructure that is created and torn down with the composition [2][3].

A **tier** is a consolidated stack that bundles related AWS services into a single CloudFormation template. The backend tier, for example, bundles Lambda, API Gateway v2, DynamoDB, and CloudWatch. Services within a tier are wired internally through CloudFormation references — no cross-stack parameters are needed. Feature flags (`Enable*` parameters, defaulting to `false`) toggle optional resources within a tier without requiring separate stacks [3].

The `/ipa-compose` skill assembles selected stacks into a deployable solution. It determines the deployment order, resolves parameter wiring between stacks, and manages inter-stack dependencies automatically [2].

A typical full-stack composition includes Cognito and ECR as prepare stacks, then a backend tier and a frontend tier as deploy stacks. Adding a queue tier enables asynchronous processing — the compose skill automatically wires SQS integration into the backend and manages the deploy ordering [2][3].

### Composition

Composition is the process of assembling the selected stack configuration into executable deployment artifacts. The `/ipa-compose` skill reads the selected stacks and generates a set of Makefiles — including `prepare.mk`, `build.mk`, `deploy.mk`, `post-deploy.mk`, `env.mk`, and `test.mk` — along with a security disposition register (`SECURITY-DISPOSITION.md`) that documents known security findings and their rationale [2][3].

The Makefiles are the execution contract. The same `make deploy` target works whether the trigger is the AI agent during development, a human at a terminal, or a CI/CD pipeline in production. One way to build, one way to test, one way to deploy [1][3].

## The Builder Workflow

The core workflow is a linear sequence of four skill invocations [2]:

```
/ipa-init       →  Establish project defaults
/ipa-compose    →  Configure security, select stacks, generate Makefiles
/ipa-prepare    →  Deploy prerequisite stacks
/ipa-deploy     →  Build, deploy, and configure
```

Each step is one skill invocation. The builder does not need to understand which stacks are deployed or how they are wired — the skills and Makefiles encode that knowledge. Sensible defaults minimize configuration, and the same sequence applies regardless of which stacks are composed. `/ipa-compose` auto-runs `/ipa-init` if the project isn't initialized, and handles security provisioning on first run [1][2].

Security is a precondition, not a phase. The `/ipa-security` skill runs early in the sequence and provisions least-privilege IAM roles scoped to the composed stacks. As the composition evolves, re-running `/ipa-security` recalculates permissions from updated stack metadata [2][4]. For details on the security model, see the Skills reference documentation.

An optional sixth step, `/ipa-codepipeline`, configures a CI/CD pipeline (CodeCommit and CodePipeline) that executes the same Makefiles the builder used locally [2].

## From Builder to Customer

The builder composes and deploys during the engagement. The customer receives the generated artifacts: Makefile targets for every lifecycle phase (prepare, build, deploy, post-deploy, test, teardown), CloudFormation templates, the security disposition register, and environment configuration [1][3].

This is the Makefile-as-contract design. The same targets the builder executed are the same ones the customer's team runs — whether manually or through their own pipeline tooling. The customer adapts the output to their organizational standards: naming conventions, network configurations, compliance requirements, and deployment processes. IPA does not attempt to automate this last mile. Instead, it accelerates the path to production by providing executable, well-documented starting points that reduce the need for cloud architect intervention [1][3].

## What Comes Next

This document establishes the conceptual vocabulary for IPA. The concepts introduced here — skills, stacks, tiers, composition, and the builder-to-customer handoff — are the foundation for the detailed documentation that follows.

- **[Installation](../installation.md)** — Set up prerequisites and configure the local development environment.
- **[Quickstart](../quickstart.md)** — Deploy a full-stack composition in a single session.
- **Skills** — Per-skill reference documentation for every `/ipa-*` command.
- **Stacks** — Per-stack architecture, parameters, outputs, and deployment details.
- **Guides** — Cross-cutting workflows: composing stacks, local development, path to production.

## Sources

1. `.context/aicode.md` — project context, objectives, design patterns, scope definition
2. `.claude/skills/ipa-*/SKILL.md` — individual skill documentation (process, stack, authoring)
3. `infra/cfn/backend/backend.yml`, `frontend/frontend.yml`, `queue/queue.yml` — tier-based consolidated CloudFormation templates; `scripts/*.mk` — generated Makefiles
4. `.claude/skills/ipa.stack.*/SECURITY.md` and `scripts/SECURITY-DISPOSITION.md` — security model artifacts
