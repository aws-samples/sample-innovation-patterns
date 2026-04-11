---
title: Authoring New Guides
sidebar_position: 2
---

# Guide Format Standard

## Overview

This document defines the standard template and writing conventions for all guides in the IPA documentation. It specifies the required section structure, content rules for each section, cross-cutting style conventions, and length guidance that every guide must follow.

The intended audience is documentation authors — both human and AI — writing guides for the IPA Guides section, as well as reviewers who assess whether a guide meets the standard format. The document covers template structure, per-section rules, and writing conventions. It does not cover the content of individual guides, stack reference documentation, or the overall documentation site structure.

The format follows a playbook/how-to hybrid model, combining the minimal procedural structure recommended by the Good Docs Project [3] with operational playbook extensions — When to Use, Before/Target State, and Verification — drawn from runbook and playbook patterns [5]. This hybrid addresses the specific needs of IPA guides, which coordinate multiple stacks, skills, and environments with real failure modes, rather than simple single-action procedures.

## Design Basis

A standard format exists to ensure consistency across all IPA guides, enable efficient scanning by readers who learn the pattern once, and support AI-authored guide generation through unambiguous section semantics. The format is a hybrid of the Good Docs Project how-to template [3] — which provides the minimal viable structure of Title, Overview, Before You Start, Steps, and Conclusion — extended with three sections from operational playbook patterns [5]: When to Use This Guide, Before/Target State, and Verification. These additions reflect that IPA guides coordinate multi-tier infrastructure workflows where context, preconditions, and post-deployment validation matter as much as the steps themselves. The Divio documentation framework [1] and Google procedural writing standards [2] provide the underlying philosophy and style rules, respectively. Kubernetes task documentation [6] and Stripe integration guides [7] serve as format exemplars demonstrating the value of rigid, repeatable structure.

The existing authoring-process-skills guide (671 lines) functions as a reference document, not a guide template. Future guides should not follow its format.

Source frameworks:

- **Divio** [1] — documentation type classification; "one guide = one goal" principle
- **Google** [2] — procedural writing rules (imperative verbs, goal-before-action, result statements)
- **Good Docs Project** [3] — minimal how-to template structure
- **PagerDuty** [5] — playbook/runbook section patterns (when-to-use, before/target state, verification)
- **Kubernetes** [6] — task page structure; "Before you begin" and "What's next" patterns
- **Stripe** [7] — integration guide structure; per-path verification patterns

## Template Structure

Every IPA guide follows this section order. Each section is either **Required** (must appear in every guide) or **Conditional** (included only when the stated condition is met).

| # | Section | Status | Condition |
|---|---------|--------|-----------|
| 1 | Title | Required | — |
| 2 | Overview | Required | — |
| 3 | When to Use This Guide | Required | — |
| 4 | Before You Start | Required | — |
| 5 | Before / Target State | Required | — |
| 6 | Steps | Required | — |
| 7 | Verification | Required | — |
| 8 | Troubleshooting | Conditional | Include only when common failure modes are documented |
| 9 | Next Steps | Required | — |

The Participants/Roles section found in some playbook formats is excluded from the standard template. IPA guides assume a single builder executing the workflow.

## Section Specifications

Each specification below defines one template section: its purpose, what to include, what to avoid, and a brief example. Each specification is independently scannable — authors and reviewers can consult any specification in isolation without reading the full document.

### Title

**Purpose:** Name the single goal the guide accomplishes. The title is the contract between the guide and the reader.

**Convention:** Use short, action-oriented titles. Examples:

- "Local Development Setup"
- "Path to Production"
- "Adding a New Stack"

Do not use the strict "How to [verb] [outcome]" pattern. Short titles are more scannable in navigation and align with the naming conventions across the IPA documentation [1].

**What to avoid:** Vague titles ("Getting Started"), compound goals ("Deploy and Monitor the Backend"), or titles that describe a topic rather than a task ("CloudFormation Stacks").

### Overview

**Purpose:** State what the guide accomplishes and what the reader will have at the end.

**What to include:** One to two sentences answering: "What will I have done when I finish this guide?" The overview sets expectations for scope and outcome without providing background.

**Example:**

> This guide walks through deploying the backend tier to a development environment. By the end, the API Gateway, Lambda function, and DynamoDB table are deployed and accepting requests.

**What to avoid:** Conceptual background, architecture explanations, or motivation for the workflow. If the reader needs context, link to an explanation document. Guides are goal-oriented, not learning-oriented [1].

### When to Use This Guide

**Purpose:** Provide decision criteria so a builder can determine whether this guide applies to their situation [5].

**What to include:** Two to four bullet points describing the trigger conditions or situational context. This section distinguishes guides from each other when a builder is scanning the Guides navigation.

**Example:**

> Use this guide when:
> - You have a new IPA project initialized with `/ipa.init` and need to deploy infrastructure for the first time
> - You are adding a new environment (`stage` or `prod`) to an existing project
>
> Do not use this guide if you are updating an already-deployed stack — see "Updating a Deployed Stack" instead.

**What to avoid:** Restating the overview. The overview says *what*; this section says *when*.

### Before You Start

**Purpose:** List everything the reader needs before beginning the steps [3][6].

**What to include:** Prerequisites as a bullet list or checklist: required tools, access, `.env` variables that must be set, and any prior guides that must be completed first.

**Example:**

> Before you start, confirm the following:
> - `.env` file exists with `APP_NAMESPACE`, `APP_ENV`, and `AWS_REGION` set
> - AWS CLI is configured with credentials for the target account
> - The `/ipa.prepare` prerequisites have been deployed (see "Deploying Prerequisites")

**What to avoid:** General setup instructions such as installing the AWS CLI or configuring git. Assume competence with standard development tooling — list only IPA-specific prerequisites [1].

### Before / Target State

**Purpose:** Make the infrastructure transformation explicit by describing what exists before the guide and what will exist after [5].

**What to include:** A concise "you have X, you will have Y" description. This can be two to four sentences or a before/after table. For infrastructure guides, describe the AWS resources, stack state, or project configuration before and after.

**Example:**

> | Before | After |
> |--------|-------|
> | `.env` configured, no deployed stacks | Backend stack deployed: API Gateway endpoint live, Lambda function running, DynamoDB table created |
> | `scripts/deploy.mk` generated but not executed | All `deploy.mk` targets executed successfully |

This section is one of the hybrid additions distinguishing IPA guides from generic how-to documentation. It gives the reader a concrete picture of the state change the guide produces.

**What to avoid:** Repeating the overview or listing steps. The overview summarizes the task; this section describes the before-and-after state.

### Steps

**Purpose:** Provide the numbered procedure that accomplishes the guide's goal. This is the longest section and contains the core instructional content.

**Formatting rules** (per Google procedural writing standards [2]):

1. **Imperative verbs.** Start each step with a verb: "Clone", "Run", "Configure", "Open". Not "You should clone" or "Next, you will run."
2. **Goal before action.** State why before how: "To deploy the stack, run:" — not "Run the following command to deploy the stack."
3. **Location before action.** When relevant, state where: "In the project root directory, run:" — not "Run this (make sure you are in the project root)."
4. **Optional steps.** Prefix with "Optional:" — for example, "Optional: To enable verbose logging, add `--verbose` to the command."
5. **Result statements.** After steps that produce non-trivial output, state the expected result: "The terminal displays the stack ARN, confirming deployment."
6. **Sub-steps.** Use lettered sub-steps (a, b, c) sparingly. Do not nest deeper than one level.

**Per-step pattern** (adapted from Kubernetes task pages [6]):

1. Context sentence — what this step does and why
2. Command or configuration — in a fenced code block
3. Expected result — what the reader should see

**Example:**

> **1. Deploy the backend stack.**
>
> To create the API Gateway, Lambda function, and DynamoDB table, run the deployment target:
>
> ```bash
> make -f scripts/deploy.mk deploy-backend
> ```
>
> The command outputs stack events as they complete. When finished, it displays:
>
> ```
> Stack app-dev-backend CREATE_COMPLETE
> ```

**What to avoid:** Explanations of underlying concepts (link to reference documentation instead), screenshots (use code blocks for all commands and output), and deep nesting beyond one sub-step level.

### Verification

**Purpose:** Confirm that the guide achieved its stated goal [5][6]. Every guide includes this section.

**What to include:** Commands to run, expected outputs, or checks to perform that prove the end state was reached. This section keeps guides accountable — it answers "did this actually work?"

**Example:**

> To verify the backend is deployed and responding, run:
>
> ```bash
> curl -s "https://<api-id>.execute-api.<region>.amazonaws.com/dev/health" | jq .
> ```
>
> Expected output:
>
> ```json
> {
>   "status": "healthy",
>   "version": "1.0.0"
> }
> ```

**What to avoid:** Treating verification as optional. If a guide deploys infrastructure, it must verify that the infrastructure is functional. If verification is complex, include the most critical check and link to a more comprehensive testing guide.

### Troubleshooting

**Purpose:** Address common failure modes so the reader can self-recover without external support.

**Inclusion criteria:** Include this section only when common failure modes are documented. If no known failure modes exist for the workflow, omit the section entirely — do not include an empty Troubleshooting heading.

**Format:** Present each issue as problem → likely cause → fix. Use a table or definition list. Limit to the three to five most common issues.

**Example:**

> | Problem | Likely Cause | Fix |
> |---------|-------------|-----|
> | `CREATE_FAILED` on Lambda resource | Missing `APP_NAMESPACE` in `.env` | Add `APP_NAMESPACE=<project-name>` to `.env` and re-run |
> | API Gateway returns 403 | Cognito authorizer not configured | Deploy the Cognito stack first — see "Deploying Prerequisites" |
> | Stack stuck in `ROLLBACK_IN_PROGRESS` | Previous failed deployment | Wait for rollback to complete, then delete the stack with `/ipa.destroy` |

**What to avoid:** Speculative failure modes, edge cases encountered once, or issues requiring escalation to an administrator. Include only issues a builder can diagnose and fix independently.

### Next Steps

**Purpose:** Direct the reader to related guides, reference documentation, or logical follow-on tasks [6].

**What to include:** A short bullet list (three to five links) using "what's next" framing. For guides that deploy infrastructure, include a link to `/ipa.destroy` and stack-specific teardown documentation for rollback and cleanup. Do not inline rollback steps — link to the existing destroy documentation instead.

**Example:**

> - **Add a frontend** — see "Deploying the Frontend Tier"
> - **Set up CI/CD** — see "Path to Production"
> - **Tear down this deployment** — run `/ipa.destroy` (see "Destroying Infrastructure")
> - **Backend stack reference** — see the backend stack skill documentation for parameters, outputs, and wiring

**What to avoid:** Summarizing what was accomplished (the Verification section already confirmed the outcome) or duplicating content from other guides.

## Writing Conventions

The following rules apply across all sections of every guide. Section-specific rules appear in the Section Specifications; these conventions are cross-cutting.

**Procedural language:**

- Use second person ("you") in procedural sections [2]
- Use imperative mood for actions — "Run", "Open", "Add" — not "You should run" or "Let us add"
- Do not use "please" [2]
- Do not use directional language ("above", "below", "the following") — section content should be independently scannable [2]
- Use active voice and short sentences

**Tone and register:**

- Formal tone throughout — no contractions ("do not" rather than "don't", "it is" rather than "it's")
- Third person is acceptable in non-procedural sections (Overview, When to Use) where the reader is not performing actions
- No filler phrases ("In order to", "It should be noted that", "As mentioned previously")

**Technical content:**

- Use fenced code blocks (triple backticks) for all commands, configuration snippets, file paths, and expected output — no screenshots
- Do not hardcode tool versions or dependency versions — reference "latest" or link to release pages
- Do not include internal AWS account IDs or ARNs — use the placeholder `123456789012` for account IDs
- Define jargon on first use or link to the Key Terms glossary — do not assume the reader knows IPA-specific terminology without definition

**Admonitions** (Docusaurus syntax):

- `:::note` — supplementary information that is useful but not essential to completing the step
- `:::warning` — information the reader must know to avoid a failure or destructive action
- `:::tip` — an optional optimization or shortcut that improves the workflow but is not required

Use admonitions sparingly. If more than two admonitions appear within a single Steps section, consider whether the information belongs in the main text instead.

## Guide Scope and Length

Each guide addresses one goal. If a guide accomplishes more than one distinct objective, it should be split into separate guides linked together [1][3].

Aim for fewer than ten major steps. Longer workflows should be divided into linked sub-guides, each with its own Verification section. The following checklist helps determine when to split:

- [ ] The guide contains more than ten major steps
- [ ] The workflow spans more than two deployment stages (for example, prepare, deploy, configure, and verify across multiple environments)
- [ ] Different sections of the guide target distinct audiences or assume different levels of prerequisite knowledge

If any item is checked, split the guide. Each sub-guide should stand alone with its own Before You Start, Verification, and Next Steps sections.

## AI Authoring Guidance

The guide format is designed to support AI-authored documentation as a first-class use case. An LLM using this specification to generate or update a guide should observe the following requirements:

- **Deterministic section semantics.** Each section heading has a fixed, unambiguous meaning defined in the Section Specifications. Do not reinterpret, rename, or extend the purpose of any section. "Before You Start" always means prerequisites; "Verification" always means post-completion checks.
- **Completable from code and configuration.** An AI with access to the codebase can populate every section by reading skill files (`.claude/skills/`), CloudFormation templates (`infra/cfn/`), `.env` configuration, and pattern definitions (`patterns/`). No section requires information that exists only in a human author's memory.
- **Validatable by reviewers.** A reviewer can check each section against the specification using objective criteria — for example: "Does Before You Start list all `.env` variables required by the referenced CloudFormation template?" or "Does Verification include a command that confirms the deployed stack is functional?"
- **No creative extension.** Do not add sections not defined in the Template Structure. Do not merge sections or reorder them. The predictability of the format is itself a feature — readers and automated tools depend on consistent structure across all guides.
- **Respect conditional sections.** Include the Troubleshooting section only when documenting known failure modes. Do not generate speculative troubleshooting entries to fill the section.

## Annotated Template

Copy the template below to start a new guide. Each section contains a comment indicating what to write. Refer to the Section Specifications for detailed rules.

```markdown
# [Guide Title]

<!-- Short, action-oriented title naming the single goal this guide accomplishes. -->

## Overview

<!-- 1-2 sentences: what the guide accomplishes and what the reader will have at the end. No conceptual background. -->

## When to Use This Guide

<!-- 2-4 bullet points: decision criteria and trigger conditions for reaching for this guide. -->

## Before You Start

<!-- Bullet list of prerequisites: tools, access, .env variables, prior guides completed. IPA-specific only. -->

## Before / Target State

<!-- "You have X → you will have Y" framing. 2-4 sentences or a before/after table. -->

## Steps

<!-- Numbered, imperative steps. Each step: context sentence → command/config block → expected result. -->

### 1. [First step summary]

<!-- Goal before action. Location before action. Command in code block. Result statement. -->

### 2. [Second step summary]

<!-- Continue the pattern. Prefix optional steps with "Optional:". Sub-steps (a, b, c) sparingly. -->

## Verification

<!-- Commands and expected output confirming the end state was reached. Required in every guide. -->

## Troubleshooting

<!-- CONDITIONAL: Include only when common failure modes exist. Problem → cause → fix. 3-5 entries max. Delete this section if not needed. -->

## Next Steps

<!-- 3-5 links: related guides, reference docs, /ipa.destroy for teardown. -->
```

## Sources

1. **Divio Documentation System** — [How-To Guides](https://docs.divio.com/documentation-system/how-to-guides/). Documentation type classification; establishes how-to guides as goal-oriented and distinct from tutorials, reference, and explanation.
2. **Google Developer Documentation Style Guide** — [Procedures](https://developers.google.com/style/procedures). Procedural writing standards: imperative verbs, goal-before-action ordering, result statements, second person.
3. **The Good Docs Project** — [How-To Template](https://github.com/thegooddocsproject/templates/tree/main/how-to). Minimal how-to structure: Title, Overview, Before You Start, Steps, Conclusion.
4. **Write the Docs** — [Documentation Guide](https://www.writethedocs.org/guide/). Community best practices; echoes the Divio documentation framework.
5. **PagerDuty** — [What Is a Runbook?](https://www.pagerduty.com/resources/learn/what-is-a-runbook/). Runbook and playbook section patterns: when-to-use, before/target state, verification, rollback.
6. **Kubernetes** — [Tasks Documentation](https://kubernetes.io/docs/tasks/). Exemplar task-based structure: "Before you begin" prerequisites, per-step explain/config/execute/verify pattern, "What's next" links.
7. **Stripe** — [Accept a Payment](https://docs.stripe.com/payments/accept-a-payment). Exemplar integration guide: parallel implementation paths, per-path prerequisites through verification.
