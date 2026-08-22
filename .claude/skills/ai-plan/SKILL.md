---
name: ai-plan
description: "Create a comprehensive implementation plan for a feature, with phases, code samples, and testing strategy. Invoke ONLY via the /ai-plan slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."

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
   - Extract `output_path` from frontmatter (default: `docs/working`) and use it as `<output_root>`
   - If `output_path` is not a string, WARN: "output_path in `.context/README.md` is not a string. Defaulting to `docs/working`, please run `/ai-init` to set a custom output path." Do NOT block — this is a warning, not a hard gate. The STOP above applies only to a missing context file.
   - Extract from top-level: Objectives, Constraints, Key Terms, References
   - For tech context (stack, patterns, testing), read `CLAUDE.md` if present

2. Resolve feature folder from `$ARGUMENTS`
   - Resolve the folder. Obtain today's date with `date +%F`.
     a. EXACT — if `<output_root>/<typed-name>/` exists, use it. Stop here.
     b. DATED-SUFFIX — list `<output_root>/` and collect entries matching
        `????-??-??-<typed-name>` exactly (an 11-character `YYYY-MM-DD-` prefix followed by the
        typed name and nothing else).
        - Exactly one match: use it. Tell the user which dated folder resolved.
        - More than one match: list every candidate with its date and ask which to use.
          Never silently pick one, and never pick the newest by default.
     b2. ARCHIVE PROBE — before auto-creating, check `<output_root>/.archive/` for an
         exact or dated-suffix match on the same name. On a hit, tell the user the folder
         is archived, print the restore command
         (`mv <output_root>/.archive/<match> <output_root>/<match>`, or `git mv` if the
         working root is tracked), and ask whether to restore it or create a new folder.
         Never auto-create silently over an archived name.
     c. AUTO-CREATE — only when neither (a) nor (b) matched, create
        `<output_root>/<today>-<typed-name>/`.

     The date in a folder name records its CREATION. Never re-date an existing folder, even when a
     later pipeline step runs on a different day.

     Do not skip step (b). A dated folder holding this feature's `research.md` is invisible to an
     exact-match-only lookup, so falling straight through to (c) would produce a second empty folder
     and a plan built without the research sitting next door — and report success.
   - Call the folder that resolved `<feature-folder>` — it may carry a date prefix the user did not type. Every path below uses it.
   - If neither (a) nor (b) matched:
     1. Create the folder: `mkdir -p <output_root>/<today>-<feature-name>/`
     2. Write a minimal `<output_root>/<today>-<feature-name>/README.md` (frontmatter `title` is the
        full dated folder name):

        ```
        ---
        title: <today>-<feature-name>
        ---

        # <Feature Title>

        ## Description
        <Derive 1-2 sentences from the feature name and project context.>

        ## Requirements
        <Infer key requirements from the feature name and .context/README.md.>

        ## Affected Areas
        <Infer from the feature name, CLAUDE.md if present, and the structure of the codebase.>

        ## Status
        - [ ] Research
        - [ ] In progress
        - [ ] Complete
        ```

        Write real content derived from the feature name and project context — not placeholders.

     3. Tell the user: "No feature folder found. Auto-created `<output_root>/<today>-<feature-name>/` with a README.md. Proceeding with planning."
   - Read `<feature-folder>/README.md` for feature identity and requirements
   - Read `<feature-folder>/research.md` (if exists) — build on findings
   - Read `<feature-folder>/design.md` (if exists) — build on architecture decisions
   - If `graphify-out/graph.json` exists: consult graph for dependency relationships and integration points. See `ai-skills-reference/graphify-integration.md`. Read `GRAPH_REPORT.md` god nodes to inform phase ordering.

## Constitution Check

**ultrathink** — A missed constraint violation becomes a blocking issue at implementation time. Cross-reference every pattern and constraint systematically.

Before generating the plan, validate against the project's coding constitution:

1. **Extract tech patterns** from `CLAUDE.md` if present, plus the conventions evident in the code you will modify
   - FOR each pattern: "Can the plan structure enforce this?"
   - IF yes: ensure the plan follows it
   - IF no: add WARNING to Validation Notes
   - IF no tech context exists at all: note that in Validation Notes and continue — a missing `CLAUDE.md` is not a blocker

2. **Extract Constraints** from `.context/README.md`
   - FOR each Constraint: "Will any planned phase violate this?"
   - A constraint is **inferred** when its bullet ends in the literal suffix `*(inferred)*` — `/ai-init` writes that marker on any constraint it derived rather than confirmed with the user. Anything without the suffix is **confirmed**.
   - IF yes AND the constraint is inferred:
       add a WARNING to Validation Notes naming the constraint and the phase.
       Continue planning — an unconfirmed inference is not a gate.
   - IF yes AND the constraint is confirmed:
       STOP and revise the plan to comply.
   - IF no: continue

3. **Extract accepted decisions from the project's ADR log** — the directory of architectural decision records it keeps, one file per decision. Resolve it as `ai-skills-reference/adr-format.md` §11 specifies: `.adr-dir` if present (its contents, resolved relative to the level that held it), else an existing `doc/adr` directory, else **no log exists**. A project with no log is the normal case — skip this step **silently**, because a warning on every run in a project that has made no architectural decisions is noise.
   - Read each record's status as the prose body of its `## Status` section, taking the keyword case-insensitively from the first non-blank line, and apply all four tolerances from `adr-format.md` §6 — among them, match "Superceded" as well as "Superseded", and treat a supersession link carrying no keyword at all as superseded. Without them a record the `adr` CLI already retired reads as live, and this check stops a plan to comply with a decision the team already replaced.
   - Map each status onto the **same two-tier ladder** step 2 runs, not a second one:
     - `Accepted` → behaves as a **confirmed** constraint. IF a planned phase violates it: STOP and revise the plan to comply.
     - `Proposed` → behaves as an **inferred** constraint. IF a planned phase violates it: add a WARNING to Validation Notes naming the record and the phase, and continue.
     - `Rejected`, `Superseded`, `Deprecated`, and log4brains' `draft` → not a constraint. Load nothing and print nothing.
     - Anything else → not a constraint, and **reported once** naming the filename and the offending value. Both silent defaults fail: reading it as `Accepted` turns a typo into a hard gate on a decision nobody made, and reading it as absent lets a real decision quietly stop gating.
   - Name the violated record **by filename** in every warning and every stop, so the user can open it. Dated record filenames carry no short identifier to cite.
   - **Read a status; never write one.** `Accepted` is the tier that stops this skill, so a planner able to accept a record would let the pipeline grant hard-gate authority to its own output. Moving a record is `/ai-adr`'s job and needs an explicit human instruction.

4. Document all warnings in the Validation Notes section

## Research Integration

If `<feature-folder>/research.md` exists:
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

   **4b. Generate Paste-Ready Phase Specs** — For each implementation phase, synthesize a self-contained paste-ready block inside a ` ```text ` fence under a `### Phase Spec (Paste-Ready)` heading at the end of the phase:

   - **Change-Name**: Generate a kebab-case name: `phase-N-<2-3-word-summary>` (e.g., `phase-1-data-models`, `phase-3-api-endpoints`).
   - **Context**: State what prior phases produced. Phase 1 says "Starting from current codebase state." Later phases name specific outputs ("Phase 2 established the data models at src/models/").
   - **Objective**: Condense the phase's Objective to one sentence.
   - **Scope**: List every file from the phase with CREATE/MODIFY annotation and brief purpose.
   - **Tasks**: Condense the phase's Tasks to independently actionable steps. Include enough detail that an external tool can execute without reading the surrounding plan.
   - **Acceptance Criteria**: Reframe the phase's Verification as human-observable outcomes. Use runnable commands, observable behaviors, or confirmable states — not implementation assertions.
   - **Scenarios**: If the plan includes a Behavioral Specification section, include 1-2 scenarios relevant to this phase's scope. Omit if no scenarios apply.
   - **Code snippets**: If the Code Implementation Samples section has a sample critical to this phase (<20 lines), include it. Omit for phases without critical structural decisions.

   Each paste-ready block must be fully self-contained — no "see above", no external references, no assumption that the reader has access to the surrounding plan. The block is a handoff artifact for external SDD tools (openspec, speckit, Kiro SDD) — users copy it directly into those tools without editing.

5. **Formulate Human-in-the-Loop (HITL) Review** — Before finalizing the plan, formulate three categories of feedback items. The emitted heading expands the abbreviation on first use — a reader of the artifact has no reason to know it:

   **Steering Opportunities (S)** — Directions this plan committed to that the user should confirm:
   - Phasing decisions (what goes first, what can wait)
   - Architectural choices (patterns, data flow, integration approach)
   - Scope trade-offs embedded in the plan
   - Frame as approve/veto/redirect. Each item: short label + one-sentence context + 2-4 choices.

   **Outstanding Questions (Q)** — Unresolved implementation decisions:
   - Always generate at least 2 unless the feature is completely unambiguous. Aim for 2-10.
   - Each must be actionable: state what decision is needed, options, and why it matters for implementation.
   - State the plan decision or trade-off the item rests on, and its consequence for implementation — not where that decision lives. A reader on the two-minute path reads this block first and may read nothing else, so an item that defers to another section is undecidable at the point of lowest patience.
   - Include a recommendation where the plan or research supports one, marked *(recommended)*.
   - Categorize (e.g., Architecture, Scope, Testing, Integration) when 5+.
   - Frame as A/B/C/D choices, not open-ended prose.

   **KISS/YAGNI Check (K)** — Based on the KISS Opportunities analysis:
   - Present each simplification opportunity as a choice: simplify or keep as planned.
   - Restate the simplification each item offers — what would be cut and what is gained — so the item reads on its own rather than sending the reader to the KISS Opportunities section for its substance.

   **Item guidelines:**
   - Target 2-5 items per subsection. No forced minimum — include a subsection only when genuine items exist.
   - Each item: 2-4 choices (A/B minimum, A/B/C/D maximum).
   - Exactly one choice per item MUST be marked *(recommended)*. This is the default applied when the user does not override the item.

**Behavioral Specification conditionality:** Include the Behavioral Specification section only when `research.md` contains a "Behavioral Scenarios" section OR the feature README contains behavioral indicators (user-facing flows, state transitions, validation, authorization, CRUD, process orchestration, domain rules). For infrastructure/refactoring features, omit it and renumber the sections that follow so the numbering stays contiguous. Refer to a section by its title rather than its number anywhere else in this skill: the ordinal a section holds depends on whether this one is present.

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
Each scenario above is a pass/fail acceptance criterion. The implement skill's Final Verification step confirms every scenario is satisfied by the implementation.

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

Each phase ends with a paste-ready spec block for external SDD tool handoff:

### Phase Spec (Paste-Ready)

` ``text
Phase: <Phase Title>
Change-Name: <kebab-case-phase-name>
Context: <What exists before this phase — prior phases completed, dependencies available>
Objective: <One-sentence goal>

Scope:
- <file/path> — CREATE/MODIFY — <brief purpose>

Tasks:
1. <Implementation step with enough detail to act on independently>
2. <Next step>

Acceptance Criteria:
- [ ] <Human-verifiable check — a command to run, a behavior to observe, or a state to confirm>
- [ ] <Next check>

[When applicable — 1-2 relevant Given/When/Then scenarios from the Behavioral Specification section]
[When applicable — brief code snippet (<20 lines) showing key structure]
` ``

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

> Keep it simple, stupid (KISS) — and you aren't gonna need it (YAGNI). Where the plan can do less and still meet the objective.

- Simplification opportunities with impact analysis

## Human-in-the-Loop (HITL) Review

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

> **K** = KISS/YAGNI — keep it simple; you aren't gonna need it. Based on the analysis above, choose whether to simplify.

K1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)*

---
*No response = all *(recommended)* defaults applied. Override format: `S1.B, Q3.C` (only the items you want to change). Free-form feedback also accepted. Resolve before running `/ai-implement`.*
```

## Output Location

**Voice pre-write check.** When the plan exceeds roughly 300 lines, run the Pre-Write Verification step from `ai-skills-reference/voice.md` before writing to file: sample 3-5 sentences from the final third, confirm each term is defined where it first appears, confirm each finding states its consequence, and confirm each reference to another part of the plan carries that part's substance. Fix a failing sentence and check its neighbours — drift is systematic. Skip this below ~300 lines.

Write the plan to `<feature-folder>/plan.md` — the folder that resolved in Context Loading, date prefix included. Never write to `<output_root>/<typed-name>/` when the resolved folder was a dated match.

## Status Tracking

After completing the plan:
1. Read the feature's README.md
2. Find the Status section
3. Update: `- [x] In progress` (the 3-item Status ladder is Research / In progress / Complete; `Complete` is checked by a human, never by a skill)
4. Use the Edit tool to update (preserve all other content)

## Manifest Update

After updating status, update the working manifest at `<output_root>/README.md`:

1. Read `<output_root>/README.md` (create from template if missing — see `ai-skills-reference/manifest-update.md`)
2. Read this feature's README.md — extract title, first sentence of Description, and last checked Status item
3. Find or append the row for this folder in the table (maintain alphabetical order — for `YYYY-MM-DD-` names this is also chronological order, oldest first; undated legacy rows sort after dated ones because digits precede letters in ASCII)
4. Determine state emoji from the 4-state ladder in `ai-skills-reference/manifest-update.md`: 🆕 (README only) → 🔬 (Research) → 🛠️ (In progress) → ✅ (Complete)
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

- **Voice**: Read `ai-skills-reference/voice.md` before writing and apply its core rules. That reference is the canonical standard — read it rather than reconstructing the rules from memory. `plan.md` is a working artifact, so the deliverable overlay does not apply. The concision rules below sharpen the prose; they never license dropping a concept the plan needs.
- **Token budget**: Plans must stay under 24,000 tokens
- **Paste-ready blocks**: Each adds ~150-250 tokens. For plans with 10+ phases, keep blocks concise (target <150 tokens each).
- Be concise and direct — every sentence must add value
- Use bullet points over prose
- Write in imperative mood ("Create", "Modify", "Implement")
- Avoid ambiguous terms ("maybe", "possibly", "could consider")

## Confirm and Guide

After writing the plan, tell the user:
- Plan location
- Number of phases
- Key architectural decisions
- "Run `/ai-implement <feature-name>` to build the feature"
