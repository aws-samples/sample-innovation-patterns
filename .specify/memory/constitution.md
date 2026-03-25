<!--
  Sync Impact Report
  ==================
  Version change: N/A (template) → 1.0.0 (initial population)
  Modified principles: N/A (first fill)
  Added sections:
    - 7 Core Principles (I–VII)
    - Constraints (security, code quality, scope)
    - Development Workflow (testing, naming, KISS)
    - Governance rules
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md — ✅ compatible (Constitution Check
      section is a generic gate; no updates needed)
    - .specify/templates/spec-template.md — ✅ compatible (requirements and
      success criteria align with accuracy/security principles)
    - .specify/templates/tasks-template.md — ✅ compatible (phase structure
      and test-first guidance align with principles III and VI)
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

Infrastructure MUST be composed from independent, modular stacks. Each
stack wraps one primary AWS service. Patterns compose stacks into
deployable solutions.

- Stacks communicate exclusively through CloudFormation output exports.
- A stack MUST NOT reference another stack's internals — only exported
  values.
- Pattern definitions encode deployment order, parameter wiring, and
  inter-stack dependencies.
- Adding or removing a stack from a pattern MUST NOT require modifying
  other stacks.

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
- Makefiles invoke Python utilities in `utils/` via `uv run` for AWS
  API operations.

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
- All stack names MUST follow `{namespace}-{app_env}-{service}`
  convention.
- Unit tests required for `utils/` Python utilities; test files
  co-located (`module.py` -> `test_module.py`).
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

The core path is four steps, executed in sequence:

1. `/ipa.init` — configure project defaults (.env, AWS profile, region)
2. `/ipa.security` — provision or update IAM roles (auto-detects mode)
3. `/ipa.compose` — select pattern, generate skill + Makefiles + runbook
4. `/ipa.deploy` — build and deploy via `scripts/build.mk` and
   `scripts/deploy.mk`

Each skill does one thing. The builder does not choose between init and
update modes — skills auto-detect.

### Testing Discipline

- pytest for all Python tests in `utils/`.
- CloudFormation templates validated with cfn-lint.
- ASH (Automated Security Helper) scanning in CI pipeline.
- DSR evaluates templates against per-service security question banks.
- Integration tests (deploy-and-verify) run manually, not as mandatory
  gates.

### KISS Principle

- Prefer simple Make targets over complex orchestration.
- Start simple; do not design for hypothetical future requirements.
- Four-step workflow — complexity is hidden from the builder.
- Stack teardown follows reverse deployment order to respect
  cross-stack references.

### Naming Conventions

- Stack names: `{namespace}-{app_env}-{service}`
- CloudFormation exports: `${AWS::StackName}-OutputKey`
- Skill files: `.claude/skills/ipa.{type}.{name}.md`
- Templates: `infra/cfn/{service}.yml`
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

**Version**: 1.0.0 | **Ratified**: 2026-03-25 | **Last Amended**: 2026-03-25
