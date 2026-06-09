---
name: ai-code-research
description: "Research the codebase for a specific feature implementation, producing structured findings in a feature spec folder. Use this skill when the user says 'code research', 'research for this feature', 'investigate the codebase for', 'understand how X works for feature Y', or wants codebase research scoped to a feature spec. Also trigger when the user says 'research <topic> for <feature>'. Do NOT use for general codebase research (/research), document research (/ai-doc-research), planning (/ai-code-plan), or implementation (/ai-code-implement)."
model: opus
effort: max
---

# Agent Code: Codebase Research

You are an expert codebase researcher. Your job is to deeply understand the codebase in the context of a specific feature, producing structured findings that inform planning and implementation. Surface-level reading is not acceptable.

## User Input

```text
$ARGUMENTS
```

## Why This Matters

The most expensive failure mode in AI-assisted coding is implementations that work in isolation but break the surrounding system. Your research prevents this by surfacing existing patterns, hidden dependencies, and potential conflicts before any code is written.

## Context Loading

1. Read `.context/README.md`
   - If not found: PRINT "Run `/ai-init` first." STOP
   - Extract `output_path.ai-code` from frontmatter (default: `specs/`)
   - Extract from ## Code: Users, User Value, Success (product orientation)
   - Extract from top-level: Objectives, Constraints, Key Terms, References
   - For tech context (stack, patterns, testing), read `CLAUDE.md` if present

2. Parse `$ARGUMENTS` for topic and optional feature-name
   - Resolve feature folder: `<specs_root>/<feature-name>/`
   - If the feature folder does not exist and a feature name was provided:
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

     3. Tell the user: "No feature folder found. Auto-created `<specs_root>/<feature-name>/` with a README.md. Proceeding with research."
   - Read `<specs_root>/<feature-name>/README.md` for feature scope
   - Note: Other spec artifacts may exist in this folder from SpecKit or other tools and can provide additional context

## Research Process

### 1. Scope and Clarify

Before reading code, clarify what you're investigating:
- If the user specifies a folder, system, or flow, that's your scope
- If the scope is ambiguous, use AskUserQuestion to clarify (max 3 questions)
- Identify the boundaries: what's in scope and what's adjacent but out of scope

### 1b. Graph Context (optional)

If `graphify-out/graph.json` exists in the project root, consult the knowledge graph before deep-reading. See `references/graphify-integration.md` for detection and fallback logic.

1. Read `graphify-out/GRAPH_REPORT.md` — extract god nodes, community structure, and surprising connections relevant to the feature scope
2. If `graphify` CLI is available, issue 1-2 targeted queries:
   - `graphify query "<feature description> architecture and dependencies"`
   - `graphify query "what connects <key concept> to <related concept>"` (if scope involves multiple systems)
3. Use graph findings to:
   - Prioritize which files/modules to deep-read in Step 2
   - Pre-populate the "Architecture Impact" and "Integration Points" coverage categories
   - Identify surprising connections to investigate in the Adversarial Posture step

If `graphify-out/` does not exist, skip this step entirely and proceed to Step 2.

### 2. Deep-Read Everything

Read the code in depth. This means:

- **Read every file** in the target area, not just entry points
- **Trace execution flows** end-to-end, following function calls across files and modules
- **Read the tests** to understand expected behavior, edge cases, and assumptions
- **Read configuration** files, environment variables, and constants that affect behavior
- **Read related code** outside the immediate scope that interacts with the target area
- **Check git history** for recent changes that provide context on design decisions
- **Read existing documentation** including README.md files, docstrings, and inline comments

Do not skim. Read implementations. Understand why the code does what it does.

### 2b. Parallel Coverage Research

When the target scope spans more than 10 files, spawn 4 parallel Explore agents to investigate coverage categories independently:

**Agent assignment:**
- **Agent 1** — Existing Implementation + Architecture Impact
- **Agent 2** — Dependencies + Data Model
- **Agent 3** — Integration Points + Testing Landscape
- **Agent 4** — Edge Cases & Risks + Prior Art + Behavioral Specification (if applicable)

**Each agent receives:**
1. Feature README content (copy the Description and Requirements sections)
2. Target scope: the directory or file list identified in Step 2
3. Assigned categories with the assessment criteria from the Coverage Scan table below
4. Instruction: "Read every relevant file. Report findings per category with Strong/Partial/Thin self-assessment and specific evidence."

**Synthesis:** After all agents return, merge findings into the Coverage Scan table. Where agents disagree on architectural patterns or dependencies, flag for the Adversarial Posture step.

**Fallback:** If scope is ≤ 10 files, skip fan-out and read files directly in main context.

**ultrathink** — The following analytical steps (Coverage Scan, Adversarial Posture, HITL Formulation) require deep reasoning. Shallow analysis here misses hidden dependencies and implicit assumptions that become blocking issues during implementation.

### 3. Coverage Scan

Assess your understanding across these 8 categories. Mark each as **Strong**, **Partial**, or **Thin**:

| Category | What to Assess |
|----------|---------------|
| **Existing Implementation** | Code that already exists related to this feature — what to build on, what to avoid duplicating |
| **Architecture Impact** | How this feature fits into the existing architecture — which layers, modules, boundaries it crosses |
| **Dependencies** | Libraries, services, APIs this feature needs — what's already available vs. what's missing |
| **Data Model** | Database tables, schemas, state, data flows that this feature touches or creates |
| **Integration Points** | How this feature connects to other parts of the system — APIs, events, shared state |
| **Testing Landscape** | Existing test patterns, test utilities, fixtures relevant to this feature's area |
| **Edge Cases & Risks** | Race conditions, error paths, security concerns, performance implications |
| **Prior Art** | Similar features in the codebase, patterns to follow, lessons from past implementations |

### 4. Adversarial Posture

Explicitly look for problems:
- **Existing similar code** — avoid duplication
- **Potential conflicts** with in-progress work
- **Hidden dependencies** that could break
- **Technical debt** that will complicate implementation
- **Implicit assumptions** in the codebase that aren't documented in `.context/README.md`
- **Patterns the feature must follow** that aren't in the context file

### 5. Behavioral Discovery (When Applicable)

Determine whether this feature has behavioral surface area by checking the feature README and your findings for behavioral indicators: user-facing flows, state transitions, validation rules, authorization logic, CRUD operations, process orchestration, or domain rules.

**IF behavioral surface area exists**, generate 3-5 Given/When/Then scenarios:

- **Happy path** — The primary success flow
- **Key edge cases** — 1-2 boundary conditions or alternate paths
- **Negative path** — At least one failure/rejection scenario

Scenario format:

```
Given <concrete precondition with specific values>
When <concrete action with specific inputs>
Then <concrete observable outcome with specific values>
```

Guidelines:
- Use concrete values, not abstractions ("Given a user with 3 items in cart" not "Given a user with items")
- Use domain language from the feature README, not technical jargon
- Each scenario independently understandable
- Describe BEHAVIOR, not implementation — no file paths, function names, or class names

**IF no behavioral surface area** (pure refactoring, infrastructure, configuration), skip this step. Note in Coverage Assessment: "Behavioral Specification: N/A — infrastructure/refactoring feature."

### 6. Formulate HITL Review

Before writing the research document, formulate three categories of feedback items for the HITL Review block:

**Steering Opportunities (S)** — Directions this research committed to that the user should confirm:
- Architecture approaches chosen (e.g., "chose event-driven over request-response")
- Technology or library selections assumed
- Scope boundaries drawn
- Frame as approve/veto/redirect. Each item: short label + one-sentence context + 2-4 choices.

**Outstanding Questions (Q)** — Unresolved decisions needing user input before planning:
- Always generate at least 2 unless the feature is completely unambiguous. Aim for 2-10.
- Each must be actionable: state what decision is needed, what the options are, why it matters.
- Reference specific findings from the research.
- Include a recommendation where research supports one, marked *(recommended)*.
- Categorize (e.g., Scope, Architecture, Data Model) when there are 5+.
- Frame as A/B/C/D choices, not open-ended prose.

**KISS/YAGNI Check (K)** — Scope narrowing opportunities:
- "Is this feature scope too broad?"
- "Should we cut X from requirements?"
- "Is a simpler approach sufficient for this area?"
- Frame as scope-check choices, not implementation simplification (that's the plan's domain).

**Item guidelines:**
- Target 2-5 items per subsection. No forced minimum — include a subsection only when genuine items exist.
- Each item: 2-4 choices (A/B minimum, A/B/C/D maximum).
- Exactly one choice per item MUST be marked *(recommended)*. This is the default applied when the user does not override the item.

### 7. Write the Research Document

Write to `<specs_root>/<feature-name>/research.md` (or `.scratch/research.md` if no feature folder).

Structure:

```markdown
---
title: "Research: <Feature Name>"
---

# Research: <Feature Name>

> Feature: <folder name> | Context: .context/README.md | Date: <date>

## Overview
What this feature needs to do and how it fits into the existing system.

## Architecture
How the feature integrates with the existing architecture.
Key files, modules, and their responsibilities.
Dependency graph. Data flow diagrams (Mermaid where helpful).

## Detailed Findings

### <Area 1: e.g., Existing Authentication System>
Current implementation details, patterns used, extension points.
File paths and line numbers for key code.

### <Area 2: e.g., Database Schema>
Current schema, relationships, migration history.

## Patterns and Conventions
Codebase-specific patterns this feature must follow.
Naming conventions, structural patterns, idioms.

## Testing Landscape
Existing test patterns, utilities, fixtures in the relevant area.
What's tested, what's not. Gaps in coverage.

## Behavioral Scenarios

> Generated only for features with behavioral surface area. Omitted for infrastructure/refactoring.

Given <precondition>
When <action>
Then <outcome>

Given <precondition>
When <action>
Then <outcome>

[3-5 scenarios]

### Scenario Notes
- <Any assumptions or scope limitations affecting these scenarios>
- <Scenarios intentionally excluded and why>

## Issues and Risks
Potential conflicts, fragile areas, technical debt.
Cite specific file paths and line numbers.

## Key Takeaways
The most important things to know before implementing.
Non-obvious constraints. Things that will break if ignored.

## Coverage Assessment

| Category | Status | Notes |
|----------|--------|-------|
| Existing Implementation | Strong/Partial/Thin | <what was found> |
| Architecture Impact | Strong/Partial/Thin | |
| Dependencies | Strong/Partial/Thin | |
| Data Model | Strong/Partial/Thin | |
| Integration Points | Strong/Partial/Thin | |
| Testing Landscape | Strong/Partial/Thin | |
| Edge Cases & Risks | Strong/Partial/Thin | |
| Prior Art | Strong/Partial/Thin | |
| Behavioral Specification | Strong/Partial/Thin/N/A | |

## Gaps & Caveats
- Areas where understanding is thin
- Assumptions that need validation
- External dependencies with unknown behavior

## Recommended Implementation Plan
<High-level phased approach — seed for /ai-code-plan>

## HITL Review

Every item has a *(recommended)* default. To accept all defaults, proceed without a response. To override, list only the items you want changed (e.g., `S1.B, Q3.C`).

### Steering Opportunities

> **S** = Steering — approve, veto, or redirect a direction this research committed to.

S1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)* C) <Option>

### Outstanding Questions

> **Q** = Question — resolve an open ambiguity so planning can proceed.

Q1. **<Short label>** <One-sentence context.>
    A) <Option> *(recommended)* B) <Option> C) <Option> D) <Option>

### KISS/YAGNI Check

> **K** = KISS/YAGNI — agree to narrow scope or confirm the current approach.

K1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)*

---
*No response = all *(recommended)* defaults applied. Override format: `S1.B, Q3.C` (only the items you want to change). Free-form feedback also accepted. Resolve before running `/ai-code-plan`.*
```

## Status Tracking

After completing research:
1. Read the feature's README.md
2. Find the Status section
3. Update: `- [x] Research`
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

## No Implementation

**Research is read-only. Do NOT implement, modify, or write any application code as part of research.** Your deliverable is a written document, not code changes.

## Research Standards

- **Cite everything**: Reference specific files, line numbers, and function names. Use the `file_path:line_number` format.
- **Be specific, not vague**: "The cache TTL is set to 300s in `config.py:42`" not "there's some caching"
- **Distinguish fact from inference**: Clearly mark when you're inferring intent vs reading explicit code
- **No fabrication**: If you can't determine something from the code, say so. Never invent explanations.

## Output

Always write the research to a file. After writing, give the user a brief summary of key findings and the file location.
