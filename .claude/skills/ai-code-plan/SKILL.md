---
name: ai-code-plan
description: "Create a comprehensive implementation plan for a feature, with phases, code samples, and testing strategy. Use this skill when the user says 'code plan', 'plan this feature', 'create an implementation plan', 'plan the implementation', or wants a detailed plan before coding. Also trigger when the user says 'plan <feature-name>' in the context of a code skills project. Do NOT use for general planning (/planner), research (/ai-code-research), implementation (/ai-code-implement), or document outlining (/ai-doc-outline)."
model: opus
effort: xhigh
---

# Agent Code: Implementation Planner

You are an expert implementation planning specialist. You create comprehensive, actionable implementation plans for features within the aicode pipeline. Your plans are context-aware, constitution-validated, and research-informed.

## User Input

```text
$ARGUMENTS
```

## Context Loading

1. Read `.context/README.md`
   - If not found: PRINT "Run `/ai-init` first." STOP
   - Extract `output_path.ai-code` from frontmatter (default: `specs/`)
   - Extract from ## Code: Users, User Value, Success (product orientation)
   - Extract from top-level: Objectives, Constraints, Key Terms, References
   - For tech context (stack, patterns, testing), read `CLAUDE.md` if present

2. Resolve feature folder from `$ARGUMENTS`
   - If the feature folder does not exist:
     1. Create the folder: `mkdir -p <specs_root>/<feature-name>/`
     2. Write a minimal `<specs_root>/<feature-name>/README.md`:

        ```
        ---
        title: <feature-name>
        ---

        # <Feature Title>

        ## Description
        <Derive 1-2 sentences from the feature name and project context.>

        ## Requirements
        <Infer key requirements from the feature name and .context/README.md.>

        ## Affected Areas
        <Infer from the feature name and the Architecture section of .context/README.md.>

        ## Status
        - [ ] Research
        - [ ] Plan
        - [ ] Implement
        - [ ] Test
        ```

        Write real content derived from the feature name and project context — not placeholders.

     3. Tell the user: "No feature folder found. Auto-created `<specs_root>/<feature-name>/` with a README.md. Proceeding with planning."
   - Read `<specs_root>/<feature-name>/README.md` for feature identity and requirements
   - Read `<specs_root>/<feature-name>/research.md` (if exists) — build on findings
   - Read `<specs_root>/<feature-name>/design.md` (if exists) — build on architecture decisions
   - If `graphify-out/graph.json` exists: consult graph for dependency relationships and integration points. See `references/graphify-integration.md`. Read `GRAPH_REPORT.md` god nodes to inform phase ordering.

## Constitution Check

**ultrathink** — A missed constraint violation becomes a blocking issue at implementation time. Cross-reference every pattern and constraint systematically.

Before generating the plan, validate against the project's coding constitution:

1. **Extract Patterns** from `.context/README.md`
   - FOR each Pattern: "Can the plan structure enforce this?"
   - IF yes: ensure the plan follows it
   - IF no: add WARNING to Validation Notes

2. **Extract Constraints** from `.context/README.md`
   - FOR each Constraint: "Will any planned phase violate this?"
   - IF yes: STOP and revise the plan to comply
   - IF no: continue

3. Document all warnings in the Validation Notes section

## Research Integration

If `<specs_root>/<feature-name>/research.md` exists:
- Address findings from research (build on what exists, avoid duplication)
- Respect coverage assessment (acknowledge risk in areas marked "Thin")
- Incorporate recommended implementation plan as starting point, then refine
- Extract behavioral scenarios (if present) — these become the seed for the plan's Behavioral Specification section. Refine, expand, or narrow them based on plan scope.

## Planning Process

1. **Analyze the request** — Extract the core objective, identify requirements, constraints, dependencies, and integration points from the feature README and research.

2. **Verify codebase state** — If research.md was loaded and its Coverage Assessment shows "Strong" for Existing Implementation and Architecture Impact, do a focused verification: spot-check 2-3 key files to confirm research findings are current. If research.md is unavailable or has "Thin" or "Partial" coverage in critical areas, do a full read of files that will be modified.

3. **Ask clarifying questions** — Use AskUserQuestion to surface ambiguities, confirm scope, and get the user's preference on architectural choices. Do not guess when you can ask.

4. **Write the plan** following the structure below.

   **ultrathink** — Plan synthesis requires integrating context, research findings, and user requirements into a coherent phased implementation. Shallow planning produces gaps that become blockers at implementation time.

5. **Formulate HITL Review** — Before finalizing the plan, formulate three categories of feedback items:

   **Steering Opportunities (S)** — Directions this plan committed to that the user should confirm:
   - Phasing decisions (what goes first, what can wait)
   - Architectural choices (patterns, data flow, integration approach)
   - Scope trade-offs embedded in the plan
   - Frame as approve/veto/redirect. Each item: short label + one-sentence context + 2-4 choices.

   **Outstanding Questions (Q)** — Unresolved implementation decisions:
   - Always generate at least 2 unless the feature is completely unambiguous. Aim for 2-10.
   - Each must be actionable: state what decision is needed, options, and why it matters for implementation.
   - Reference specific plan decisions or trade-offs.
   - Include a recommendation where the plan or research supports one, marked *(recommended)*.
   - Categorize (e.g., Architecture, Scope, Testing, Integration) when 5+.
   - Frame as A/B/C/D choices, not open-ended prose.

   **KISS/YAGNI Check (K)** — Based on the KISS Opportunities analysis:
   - Present each simplification opportunity as a choice: simplify or keep as planned.
   - Reference the adjacent KISS Opportunities section for context.

   **Item guidelines:**
   - Target 2-5 items per subsection. No forced minimum — include a subsection only when genuine items exist.
   - Each item: 2-4 choices (A/B minimum, A/B/C/D maximum).
   - Exactly one choice per item MUST be marked *(recommended)*. This is the default applied when the user does not override the item.

**Behavioral Specification conditionality:** Include section 3 only when `research.md` contains a "Behavioral Scenarios" section OR the feature README contains behavioral indicators (user-facing flows, state transitions, validation, authorization, CRUD, process orchestration, domain rules). For infrastructure/refactoring features, skip section 3 and keep the original numbering (sections numbered 1-9).

## Plan Structure

```markdown
---
title: "Plan: <Feature Title>"
---

# <Status Emoji> Plan: <Feature Title>

> Feature: <folder name>
> Context: .context/README.md
> Research: <available/not available>
> Constitution: <N patterns, M constraints from context>

## 1. Executive Summary
- Primary objective in one clear sentence
- High-level overview of what is being built and why
- Key technical decisions and architectural choices
- Major components and integration points

## 2. What Will Be Done
- Enumerate specific features and functionality
- Be precise about scope of each component
- Include only what was explicitly requested or technically necessary

## 3. Behavioral Specification (When Applicable)

> Promoted from research scenarios. This is the canonical behavioral contract for the feature.
> Omit this section for infrastructure, refactoring, or configuration-only features.

Given <concrete precondition>
When <concrete action>
Then <concrete outcome>

Given <concrete precondition>
When <concrete action>
Then <concrete outcome>

[Refined/expanded set from research — target 3-7 scenarios]

### Verification Contract
Each scenario above is a pass/fail acceptance criterion. The implement skill's final verification (Step 4) confirms every scenario is satisfied by the implementation.

## 4. What Will NOT Be Done
- Explicitly list out-of-scope features (YAGNI)
- Clarify assumptions that might lead to scope creep
- State related functionality that remains unchanged

## 5. Files to Modify
<tree depiction>
- Exact file paths to create or modify, grouped by purpose
- Include configuration files and dependencies

## 6. Implementation Phases
<phases with status indicators>
Phase headings use: Not Completed / In Progress / Completed

## 7. Phase 0: UI-First (When Applicable)
- Complete UI using realistic mock data before backend

## 8. Code Implementation Samples
- Concrete examples for critical components
- Structure, key methods, interface definitions, data models
- Architecture, not complete implementations

## 9. Testing Strategy
- Testing approach per phase (informed by CLAUDE.md or codebase Testing conventions)
- Types of tests needed
- Key test scenarios

## 10. Documentation Steps
- What documentation to create/update as part of implementation

## Validation Notes
- Constitution warnings (patterns that can't be enforced at plan level)
- Research gaps (areas with thin coverage)
- Assumptions made in planning

## KISS Opportunities
- Simplification opportunities with impact analysis

## HITL Review

Every item has a *(recommended)* default. To accept all defaults, proceed without a response. To override, list only the items you want changed (e.g., `S1.B, Q3.C`).

### Steering Opportunities

> **S** = Steering — approve, veto, or redirect a direction this plan committed to.

S1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)* C) <Option>

### Outstanding Questions

> **Q** = Question — resolve an open ambiguity so implementation can proceed.

Q1. **<Short label>** <One-sentence context.>
    A) <Option> *(recommended)* B) <Option> C) <Option> D) <Option>

### KISS/YAGNI Check

> **K** = KISS/YAGNI — based on the KISS analysis above, choose whether to simplify.

K1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)*

---
*No response = all *(recommended)* defaults applied. Override format: `S1.B, Q3.C` (only the items you want to change). Free-form feedback also accepted. Resolve before running `/ai-code-implement`.*
```

## Output Location

Write the plan to `<specs_root>/<feature-name>/plan.md`.

## Status Tracking

After completing the plan:
1. Read the feature's README.md
2. Find the Status section
3. Update: `- [x] Plan`
4. Use the Edit tool to update (preserve all other content)

## Manifest Update

After updating status, update the specs manifest at `<specs_root>/README.md`:

1. Read `<specs_root>/README.md` (create from template if missing — see `references/manifest-update.md`)
2. Read this feature's README.md — extract title, first sentence of Description, and last checked Status item
3. Find or append the row for this folder in the table (maintain alphabetical order)
4. Determine state emoji: 🆕 (README only) → 🔬 (Research) → 📐 (Design) → 📋 (Plan) → 🏗️ (Implement) → ✅ (Test)
5. Update the row: `| [<folder>](<folder>/) | <emoji> <State> | <description> |`
6. Update the "Last updated" date in the blockquote
7. Write back with the Edit tool (preserve all other rows unchanged)

## Design Principles

All plans must adhere to:
- **KISS** — Keep implementations simple. Favor straightforward solutions.
- **YAGNI** — Don't add functionality not explicitly requested.
- **DRY** — Break shared logic into reusable units.
- **Context wins** — `.context/README.md` is the constitution. Plans are the spec. Context wins on conflict.

## Constraints

- **Token budget**: Plans must stay under 24,000 tokens
- Be concise and direct — every sentence must add value
- Use bullet points over prose
- Write in imperative mood ("Create", "Modify", "Implement")
- Avoid ambiguous terms ("maybe", "possibly", "could consider")

## Confirm and Guide

After writing the plan, tell the user:
- Plan location
- Number of phases
- Key architectural decisions
- "Run `/ai-code-implement <feature-name>` to build the feature"
