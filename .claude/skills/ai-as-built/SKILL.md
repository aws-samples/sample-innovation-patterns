---
name: ai-as-built
description: "Document how a feature, subsystem, or module was actually built. Invoke ONLY via the /ai-as-built slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."

effort: high
---

# Agent Code: As-Built Documentation

You produce comprehensive as-built documentation for features, subsystems, modules, or cross-cutting concerns. The goal is to create a reference that lets a developer (or a future Claude session) quickly understand exactly how something was built.

## User Input

```text
$ARGUMENTS
```

## Context Loading

1. Read `.context/README.md`
   - If not found: WARN "No project context found. Proceeding without project context." Continue anyway.
   - Extract from top-level: Objectives, Constraints, Key Terms
   - For tech context (stack, patterns), read `CLAUDE.md` if present
   - Extract `output_path` from frontmatter (default: `docs/working`) and use it as `<output_root>` — the single working root holding every folder
   - If `output_path` is not a string, WARN: "output_path in `.context/README.md` is not a string. Defaulting to `docs/working`, please run `/ai-init` to set a custom output path." Do NOT block — this is a warning, not a hard gate.

2. Check for feature folder:
   - If `$ARGUMENTS` maps to a `<output_root>/<feature-name>/` folder:
     - Read README.md for feature identity
     - Read plan.md (if exists) — note where implementation deviated from plan
     - If `graphify-out/graph.json` exists: read `graphify-out/GRAPH_REPORT.md` for pre-built architecture overview. Use graph communities as starting point for module boundary documentation and god nodes for key components. See `ai-skills-reference/graphify-integration.md`.
     - Output location: `<output_root>/<feature-name>/as-built.md`
   - Otherwise: output location is `.scratch/as-built-{name}.md`

## Process

### 1. Scope the Documentation

Clarify what you're documenting:
- The user may specify a feature, a directory, a module, or a cross-cutting concern
- If the scope is ambiguous, use AskUserQuestion to clarify before proceeding
- Identify the boundaries: what's part of this feature vs adjacent systems

### 2. Deep-Read the Implementation

Read all code related to the feature:

- **Read every file** that implements the feature, not just entry points
- **Trace data flows** from user action through components, state, API calls, and back
- **Read configuration** that affects behavior: env vars, config files, feature flags
- **Read tests** to understand expected behavior and edge cases
- **Read type definitions** and interfaces to understand contracts
- **Read adjacent code** that the feature integrates with

Focus on understanding the current state of the implementation.

### 2b. Parallel Analysis

When the implementation spans more than 10 files, spawn 3 parallel Explore agents to analyze independent aspects:

**Agent 1 (Architecture):** "Read all source files in <scope>. Report: component relationships, module boundaries, layer architecture, design patterns used, integration boundaries."

**Agent 2 (Data & Config):** "Read all source files in <scope>. Report: data flows, state management, configuration surface, environment dependencies, external service connections."

**Agent 3 (Quality & Operations):** "Read all test files and configs in <scope>. Report: test patterns, coverage areas, performance characteristics, known gotchas, error handling approaches."

Synthesize findings from all agents into the unified analysis below.

**Fallback:** If scope is ≤ 10 files, read directly in main context.

### 3. Analyze the Architecture

**ultrathink** — The quality of as-built documentation depends directly on the depth of architectural understanding. Surface-level reading produces documentation that misleads future developers.

- **Component relationships**: What depends on what?
- **Data flow**: How does data enter, transform, and exit?
- **State management**: Where does state live? What triggers changes?
- **Patterns used**: What design patterns, conventions, or idioms?
- **Configuration surface**: What's tunable vs hardcoded?
- **Integration boundaries**: Where does this feature hand off to other systems?
- **Pattern compliance**: Where does implementation follow (or deviate from) the conventions recorded in `CLAUDE.md` and evident in the surrounding code?

### 4. Write the As-Built Document

**Voice pre-write check.** When the document exceeds roughly 300 lines, run the Pre-Write Verification step from `ai-skills-reference/voice.md` before writing to file: sample 3-5 sentences from the final third, confirm each term is defined where it first appears, confirm each finding states its consequence, and confirm each reference to another part of the document carries that part's substance. Fix a failing sentence and check its neighbours — drift is systematic. Skip this below ~300 lines.

Structure the document with these sections:

```markdown
---
title: "As-Built: <Feature Name>"
---

# As-Built: <Feature Name>

## Overview
What this feature/system does. Its role in the larger application.

## Architecture
Key architectural decisions and patterns. Component organization.
Data flow (use Mermaid diagrams where helpful). External dependencies.

## File Inventory
Complete catalog of files, grouped logically. File path, responsibility, key exports.

## Implementation Details
Entry points, key algorithms, state management, API contracts,
component hierarchy, event handling, data models.
Use `file_path:line_number` format for references.

## Patterns and Conventions
Naming conventions, structural patterns, error handling, testing patterns.
Note where implementation follows or deviates from the conventions in CLAUDE.md and the surrounding code.

## Configuration and Environment
Environment variables, config files, feature flags, defaults.

## Integration Points
APIs consumed, events emitted/subscribed, shared state, dependencies.

## Maintenance and Gotchas
Non-obvious constraints, fragile areas, known limitations, common pitfalls,
order dependencies, performance considerations.
Each gotcha must be specific and actionable.

## Testing
Test files, patterns used, how to run tests, coverage gaps.

## Key Takeaways
5-10 most important things to know before modifying this feature.
```

If plan.md exists, add a section noting where implementation deviated from the plan.

## No Implementation

**As-built documentation is read-only. Do NOT implement, modify, or write any application code.** Your deliverable is a written document, not code changes.

## Documentation Standards

- **Voice**: Read `ai-skills-reference/voice.md` before writing and apply its core rules. That reference is the canonical standard — read it rather than reconstructing the rules from memory. `as-built.md` is a working artifact, so the deliverable overlay does not apply.
- **Cite everything**: `file_path:line_number` format
- **Be precise**: specific values, not vague descriptions
- **Document what is, not what should be**: factual, not aspirational
- **No fabrication**: say "unclear from code" rather than guessing
- **Be thorough**: read every file, trace every flow

## Output

Write the document to a file. After writing, give the user a brief summary and the file location.
