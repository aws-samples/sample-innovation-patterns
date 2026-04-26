<!--
  Sync Impact Report
  ==================
  Version change: 1.0.0 → 1.1.0
  Amendment rationale: spec 012-tier-stack-consolidation resolved
    JUSTIFIED VIOLATION of Principle II by expanding the principle to
    support tier-based consolidation alongside single-service stacks.
  Modified principles:
    - II. Composability — materially expanded: two stack models (prepare
      stacks + tier stacks), feature flag composability, internal wiring
    - VII. Makefile as Contract — corrected: utils/ removed, now direct
      AWS CLI + scripts/util/ helpers
  Modified sections:
    - Code Quality Constraints — stack naming updated for {identifier},
      unit test reference corrected from utils/ to app-lib/tests/
    - Naming Conventions — tier template paths added, skill file path
      corrected to directory structure
    - Builder Workflow — expanded from 4 to 6 steps (added /ipa.prepare
      and /ipa.destroy)
    - Testing Discipline — corrected utils/ reference, added
      validate-template, updated DSR language for tier-based templates
    - KISS Principle — step count updated from four to six
  Added sections: None
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md — ✅ compatible (Constitution
      Check section is a generic gate; no updates needed)
    - .specify/templates/spec-template.md — ✅ compatible (requirements
      and success criteria align with accuracy/security principles)
    - .specify/templates/tasks-template.md — ✅ compatible (phase
      structure and test-first guidance align with principles III/VI)
    - .specify/templates/checklist-template.md — ✅ compatible
    - .specify/templates/agent-file-template.md — ✅ compatible
  Follow-up TODOs: None
-->

# Innovation Patterns Agent (IPA) Constitution

## Core Principles

### I. Security First (NON-NEGOTIABLE)

All generated infrastructure and code MUST follow AWS security best
practices. Security is a precondition for every pattern, stack, and
generated artifact — not a bolt-on phase.

- No secrets or credentials in templates, code, or generated artifacts.
- No wildcard (`*`) IAM resource ARNs — all policies scoped to specific
  resources.
- No public-by-default resources (S3 buckets, Lambda URLs, API
  endpoints).
- Encryption at rest and in transit MUST be enabled by default on all
  data stores and endpoints.
- Every composed pattern MUST pass DSR security review with
  least-privilege IAM before delivery.
- `/ipa.security` MUST be run before any deployment; the agent detects
  whether to initialize or update the security posture automatically.

### II. Composability

Infrastructure MUST be composed from independent, modular stacks.
Patterns compose stacks into deployable solutions. IPA uses two stack
models:

- **Prepare stacks** wrap one primary AWS service (ECR, Cognito,
  Security). They are deployed once and shared across patterns.
- **Tier stacks** consolidate related services into a single deployable
  unit (frontend, backend, queue). Each tier is independently deployable
  and atomically updatable. Services within a tier wire together via
  `!Ref` and `!GetAtt` — internal wiring is an implementation detail
  not exposed through outputs.

Rules:

- Cross-stack communication (whether prepare-to-tier or tier-to-tier)
  uses CloudFormation output exports exclusively. A stack MUST NOT
  reference another stack's internals — only exported values.
- Feature flags within tier templates (`Enable*Table`,
  `Enable*Integration`) MUST default to disabled. Patterns explicitly
  enable the resources they need via parameter overrides at composition
  time.
- Pattern definitions encode deployment order, parameter wiring, and
  inter-stack dependencies.
- Adding or removing a stack or tier from a pattern MUST NOT require
  modifying other stacks or tiers.

### III. Human Control (Eject Capability)

The customer MUST always be able to take over from the AI agent. The
runbook and Makefiles are the eject path — they enable deployment
without IPA tooling, without the AI agent, and without the builder.

- Every `/ipa.compose` run MUST generate a current runbook at
  `docs/infra/runbook.md`.
- Every `/ipa.compose` run MUST generate self-contained Makefiles at
  `scripts/*.mk`.
- Generated Makefiles MUST NOT depend on `.env`, IPA skills, or Claude
  Code at execution time.
- A customer engineer MUST be able to deploy the infrastructure by
  following the runbook alone.

### IV. Agent-Native Design

Skills are designed for AI agents as the primary consumers.
Human-readable artifacts — runbooks, annotated Makefiles,
documentation — are generated outputs.

- Skill files (`.claude/skills/`) are the primary interface for the AI
  agent.
- Human-facing artifacts (runbook, Makefiles, DSR matrix) are generated
  by skills, not authored by hand.
- The agent composes, deploys, self-diagnoses, and self-heals; the
  builder confirms proposed actions.
- Self-healing MUST be transparent: the agent explains diagnosis and
  proposed fix before acting.

### V. Accuracy over Speed

Skills MUST deploy exactly what they are configured to deploy.
Consistency between the composed pattern, Makefiles, runbook, and actual
deployed infrastructure is the primary quality metric.

- Makefiles MUST reflect the exact stack sequence and parameters from
  the composed pattern.
- The runbook MUST document the same steps the Makefiles execute.
- CloudFormation templates MUST match resource descriptions in stack
  skills.
- IAM roles MUST match the aggregated security metadata from all stacks
  in the pattern.
- Verify consistency across all four artifacts (pattern skill,
  Makefiles, runbook, deployed state) after every compose and deploy.

### VI. Idempotency

Every skill MUST be safe to run multiple times without destroying
existing configuration, overwriting uncommitted changes, or creating
duplicate resources.

- Re-running `/ipa.compose` regenerates artifacts without losing
  deployed state.
- Re-running `/ipa.deploy` completes partial deployments rather than
  creating conflicts.
- `CreateStack` switches to `UpdateStack` if the stack exists.
- `UpdateStack` succeeds silently if no changes are detected.
- Makefile re-generation overwrites the previous version (Makefiles are
  generated, never hand-edited).

### VII. Makefile as Single Execution Contract

The Makefiles (`scripts/*.mk`) are the single source of truth for
build, test, and deploy. The AI agent, human builders, and CI/CD
pipelines MUST all execute the same targets.

- There is one way to build, one way to test, and one way to deploy.
- Generated Makefiles MUST be self-contained — values baked in at
  compose time, no runtime `.env` dependency.
- Makefiles work identically on the builder's machine, in the AI
  agent's context, and in CodePipeline.
- Makefiles invoke AWS CLI commands directly for CloudFormation
  operations. Small Python helper scripts in `scripts/util/` handle
  non-CloudFormation tasks (versioning, frontend configuration).

## Constraints

### Security Constraints (enforced by Principle I)

- No `eval()` or dynamic code execution in any generated artifact.
- All user input MUST be sanitized before database queries.
- No synchronous file I/O in request handlers.
- No GPL-licensed dependencies.
- S3 Block Public Access MUST be enabled on all buckets.
- HTTPS-only enforced on CloudFront, API Gateway, and S3 bucket
  policies.

### Code Quality Constraints

- Type-safe and strict: no `any` in TypeScript, full type hints in
  Python.
- CloudFormation templates MUST be valid standalone — no IPA-specific
  extensions or custom macros.
- All stack names MUST follow `{namespace}-{app_env}-{identifier}`
  convention, where `{identifier}` is a service name for prepare stacks
  (e.g., `ecr`, `cognito`) or a tier name for consolidated stacks
  (e.g., `frontend`, `backend`, `queue`).
- Unit tests required for `app-lib/` Python application code; test
  files in `app-lib/tests/` mirror the source directory structure.
- CloudFormation templates MUST pass cfn-lint validation.

### Scope Constraints

- IPA produces evolvable POC infrastructure, not production-grade
  systems. Do not over-engineer for production concerns (HA, multi-AZ,
  advanced monitoring) that are the customer's responsibility.
- Generated artifacts (Makefiles, runbook) MUST work without IPA or
  Claude Code.
- Single environment only (POC/dev). No multi-environment or
  multi-account support.
- AWS CloudFormation is the primary IaC tool (Tier 1). Terraform is
  Tier 2 (future). CDK is deferred.

## Development Workflow

### Builder Workflow

The core path is six steps, executed in sequence:

1. `/ipa.init` — configure project defaults (.env, AWS profile, region)
2. `/ipa.security` — provision or update IAM roles (auto-detects mode)
3. `/ipa.compose` — select pattern, generate Makefiles + runbook
4. `/ipa.prepare` — deploy prerequisite stacks (ECR, Cognito) via
   `scripts/prepare.mk`
5. `/ipa.deploy` — build and deploy via `scripts/build.mk` and
   `scripts/deploy.mk`
6. `/ipa.destroy` — tear down composed infrastructure via
   `scripts/deploy.mk` teardown targets

Each skill does one thing. The builder does not choose between init and
update modes — skills auto-detect. Prepare runs once per environment;
destroy is used when tearing down.

### Testing Discipline

- pytest for all Python tests in `app-lib/tests/`.
- CloudFormation templates validated with
  `aws cloudformation validate-template` and cfn-lint.
- ASH (Automated Security Helper) scanning in CI pipeline.
- DSR evaluates templates (both prepare and tier-based) against
  security question banks.
- Integration tests (deploy-and-verify) run manually, not as mandatory
  gates.

### KISS Principle

- Prefer simple Make targets over complex orchestration.
- Start simple; do not design for hypothetical future requirements.
- Six-step workflow — complexity is hidden from the builder.
- Stack teardown follows reverse deployment order to respect
  cross-stack references.

### Naming Conventions

- Stack names: `{namespace}-{app_env}-{identifier}` (service name or
  tier name)
- CloudFormation exports: `${AWS::StackName}-OutputKey`
- Skill files: `.claude/skills/ipa.{type}.{name}/SKILL.md`
- Templates (prepare): `infra/cfn/{service}/{service}.yml`
- Templates (tier): `infra/cfn/{tier}/{tier}.yml`
- Makefiles: `scripts/{purpose}.mk`

## Governance

This constitution supersedes all other development practices for the
IPA project. All feature specifications, implementation plans, and code
reviews MUST verify compliance with these principles.

**Amendment procedure:**
1. Propose the change with rationale referencing a specific principle.
2. Document the amendment in this file with version bump.
3. Propagate changes to dependent templates (plan, spec, tasks).
4. Update the Sync Impact Report at the top of this file.

**Versioning policy:** Semantic versioning (MAJOR.MINOR.PATCH).
- MAJOR: Principle removal or backward-incompatible redefinition.
- MINOR: New principle added or existing principle materially expanded.
- PATCH: Clarifications, wording, or non-semantic refinements.

**Compliance review:** Every feature spec and implementation plan MUST
include a Constitution Check gate that validates alignment with all
seven principles before work begins. Re-check after design phase.

**Runtime guidance:** Refer to `.context/aicode.md` for project-level
coding context and `.context/aicode-technical.md` for architectural
details.

**Version**: 1.1.0 | **Ratified**: 2026-03-25 | **Last Amended**: 2026-04-10
