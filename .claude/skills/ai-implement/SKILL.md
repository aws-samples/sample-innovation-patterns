---
name: ai-implement
description: "Execute an implementation plan for a feature by building all code specified in it. Invoke ONLY via the /ai-implement slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."

effort: xhigh
---

# Agent Code: Implementation Executor

You execute implementation plans with precision. Your job is to build exactly what the plan specifies — every phase, every file, every detail — without skipping, simplifying, or improvising beyond what's written.

## User Input

```text
$ARGUMENTS
```

## Context Loading

1. Resolve project context (in priority order):
   a. Read `.context/README.md`
      - If found: extract `output_path` from frontmatter (default: `docs/working`) and use it as `<output_root>`
      - If `output_path` is not a string, WARN: "output_path in `.context/README.md` is not a string. Defaulting to `docs/working`, please run `/ai-init` to set a custom output path." Do NOT block — this is a warning, not a hard gate.
      - Extract from top-level: Objectives, Constraints, Key Terms, References
   b. If `.context/README.md` not found — fall back to root-level context:
      - Read `README.md` (project description and orientation)
      - Read `AGENTS.md` (if exists — agent-specific guidance)
      - Read `CLAUDE.md` (if exists — tech context, patterns, testing)
      - Use defaults: `output_path` = `docs/working`
      - WARN: "No `.context/README.md` found. Using root README.md, AGENTS.md, and CLAUDE.md for context. Run `/ai-init` for richer context."
   c. If no context files found at all:
      - WARN: "No project context found. Proceeding without project context."
      - Use defaults: `output_path` = `docs/working`
   - For tech context (stack, patterns, testing), read `CLAUDE.md` if present (applies to all paths above)

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

     Do not skip step (b). A dated folder holding this feature's `plan.md` is invisible to an
     exact-match-only lookup, so falling straight through to (c) would report a missing plan for work
     that has one.
   - Call the folder that resolved `<feature-folder>` — it may carry a date prefix the user did not type. Every path below uses it.
   - Read `<feature-folder>/README.md` — feature identity
   - Read `<feature-folder>/plan.md` — the blueprint (REQUIRED)
   - Read `<feature-folder>/research.md` — additional context (optional)
   - If `graphify-out/graph.json` exists: graph is available for integration queries during implementation. See `ai-skills-reference/graphify-integration.md`. Use `graphify query "what uses <interface>"` before modifying shared interfaces.

   IF plan.md not found:
     - If neither (a) nor (b) matched — no folder resolved at all:
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

       3. Tell the user: "No feature folder found. Auto-created `<output_root>/<today>-<feature-name>/` with a README.md."

     - Use AskUserQuestion to ask how to proceed:
       - "Run /ai-plan first" — Tell the user: "Run `/ai-plan <feature-name>` to create a plan, then run `/ai-implement <feature-name>` again." STOP.
       - "Describe what to build" — Ask for a description of what to implement. Use that description plus the code context as the implementation guide. Proceed without plan-based execution (skip phase tracking, checklist sweep against plan).

     STOP after presenting options. Do not proceed without user input.

## Step 1: Analyze the Plan and Research the Codebase

**ultrathink** — This is the "measure twice" step. Missing a conflict between plan and codebase here means hitting it mid-implementation, which is far more expensive to resolve.

Before writing any code, thoroughly understand what you're building:

1. **Parse the plan** — Extract every file to create/modify, every phase, every code sample, every interface definition, every naming convention, every testing requirement. Build a mental checklist.
   - **Skip paste-ready blocks** — Phases may contain a `Phase Spec (Paste-Ready)` subsection (at any heading level, `###` or `####`) with fenced text blocks. These are handoff artifacts for external SDD tools — ignore them when extracting implementation tasks.

2. **Verify codebase state** — If research.md was loaded and its Coverage Assessment shows "Strong" for Existing Implementation and Architecture Impact, do a focused verification: read only files the plan creates or modifies to confirm they match expectations. If research.md is unavailable or has "Thin" coverage, do a full read of all files the plan references.

3. **Identify gaps and conflicts** — Compare what the plan expects vs. what the codebase actually contains. Look for:
   - Files that have changed since the plan was written
   - Dependencies the plan assumes but aren't installed
   - Interfaces or APIs that don't match what the plan describes
   - Code samples in the plan that conflict with existing patterns

## Step 2: Ask All Questions Upfront

Before writing a single line of implementation code, surface every question, ambiguity, and conflict you found. Batch them into a single AskUserQuestion call organized by category:

- **Conflicts** — Where the plan disagrees with the current codebase state
- **Ambiguities** — Where the plan is underspecified and you'd have to guess
- **Decisions** — Where you see multiple valid approaches
- **Dependencies** — Missing packages or prerequisites

If everything aligns: "I've reviewed the plan and the codebase — everything aligns. Starting implementation."

## Step 2b: Phase Independence Analysis

Before executing phases, analyze the plan for independent phases (non-overlapping files, no data dependencies between them):

1. For each pair of phases, check: do they modify any of the same files? Does one phase's output feed another's input?
2. Phases that share no files and have no data dependencies are **independent** and can be parallelized.

**For independent phases:** Spawn parallel agents (one per independent phase) using the Agent tool:
- Each agent receives: the phase specification from the plan, relevant context from `.context/README.md`, and its file scope
- Each agent implements its phase and runs local verification (lint, type-check, test if applicable)
- Main context synthesizes results, resolves any integration issues, and runs final verification

**For dependent phases:** Execute sequentially as described below.

**Fallback:** If all phases are dependent (each builds on the prior), skip parallelization and execute sequentially.

## Step 3: Implement Phase by Phase

Work through the plan's phases in order. For each phase:

### 3a. Build Everything in the Phase
Follow the plan's instructions precisely:
- **File creation** — Create every file listed, at the exact paths specified
- **File modification** — Modify exactly the files listed. Read each file before editing.
- **Code samples** — Use them as the authoritative reference for structure, naming, interfaces, and patterns
- **Naming conventions** — Use exactly the names the plan specifies
- **Dependencies** — Install any packages the plan requires
- **Configuration** — Update config files as the plan specifies

### 3b. Pattern Compliance

After completing each phase, verify the code follows the project's conventions — read `CLAUDE.md` if present for tech context, and match the patterns evident in the surrounding code:
- **Context is the constitution; plan is the spec. Context wins on conflict.**
- If `CLAUDE.md` or the surrounding code establishes a repository pattern → implement through repositories even if the plan is abstract
- If the codebase co-locates test files → place test files next to source files
- **Constraints** come from `.context/README.md`, and their authority depends on provenance. A constraint whose bullet ends in the literal suffix `*(inferred)*` was derived by `/ai-init` rather than confirmed by the user; anything without the suffix is confirmed.
  - **Confirmed** (e.g. `- No eval()`) → absolute. Never violate it, even to resolve an ambiguity in the plan.
  - **Inferred** (e.g. `- No eval() — *(inferred)*`) → follow it by default, but report it in the final summary rather than treating it as a hard gate. If the plan requires violating it, do so and say which inferred constraint you crossed and why.
- **Accepted decisions** come from the project's ADR log — the directory of architectural decision records it keeps, one file per decision. Resolve it as `ai-skills-reference/adr-format.md` §11 specifies: `.adr-dir` if present (its contents, resolved relative to the level that held it), else an existing `doc/adr` directory, else no log exists. Skip **silently** when no log exists — a project that has made no architectural decisions is the normal case. Read each status as the prose body of `## Status` with all four tolerances from `adr-format.md` §6, so a record the `adr` CLI retired — spelled "Superceded", or left holding a supersession link with no keyword at all — is not read as live. Then map onto the same ladder the constraints use:
  - **`Accepted`** → treat as a confirmed constraint. Never violate it, even to resolve an ambiguity in the plan.
  - **`Proposed`** → treat as an inferred constraint. Follow it by default and report it in the final summary.
  - **`Rejected`, `Superseded`, `Deprecated`, and log4brains' `draft`** → not a constraint. Load nothing, report nothing.
  - **anything else** → not a constraint, and reported once naming the filename and the value. Reading a typo as `Accepted` would gate on a decision nobody made; reading it as absent would let a real decision stop gating.

  Name the record **by filename** whenever you report one — dated filenames carry no short identifier to cite. **Read a status; never write one:** moving a record is `/ai-adr`'s job and needs an explicit human instruction.

### 3c. Implementation Quality
- Write complete, working code — no TODOs, no placeholder implementations
- Follow existing codebase patterns for things the plan doesn't explicitly specify
- Ensure files compile and imports resolve
- Write the tests specified in the plan's testing strategy for this phase

### 3d. Continue to Next Phase
Move immediately to the next phase. Only stop for true blockers.

## Step 4: Final Verification

After all phases are complete:

1. **Checklist sweep** — Go back through the plan section by section and verify every item was implemented:
   - Every file in "Files to Modify" was created or modified
   - Every feature in "What Will Be Done" is present in the code
   - Every test in "Testing Strategy" was written
   - Code samples in the plan are reflected in the implementation

2. **Test execution** — Detect the test command, then run it after the final phase and report results. Check in order:
   - `CLAUDE.md`, if it names a test command
   - the package manifest — `package.json` `scripts.test`, a `pyproject.toml` pytest or tox config, `Cargo.toml`, `Makefile` targets
   - an existing test directory (`tests/`, `test/`, `__tests__/`, or co-located `*_test.*` / `*.test.*` files) whose framework implies the runner

   If none of these turns up a command, say so and skip — do not invent one.

3. **Report any deviations** — If you deviated from the plan, list what you changed and why.

4. **Update the plan** — Mark all phase statuses as "Completed" and the plan's top-level status as complete.

5. **Summary** — Give the user:
   - What was built (files created/modified count)
   - Any deviations from the plan
   - Test results (if run)
   - What to verify next

## Status Tracking

After completing implementation:
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

## Handling Blocking Issues Mid-Implementation

If you encounter a genuinely blocking issue:
1. Stop and describe the specific problem
2. Explain what the plan says vs. what you're seeing
3. Propose a solution if you have one
4. Ask the user how to proceed
5. After the user responds, resume from where you stopped

## Principles

- **The plan is the spec.** Execute faithfully, don't redesign.
- **Context is the constitution.** `.context/README.md` Constraints and Key Terms win on any conflict with the plan — a confirmed constraint absolutely, an `*(inferred)*` one by default but reported.
- **Complete means complete.** Every phase, every file, every feature, every test.
- **Details matter.** Use exact names, exact paths, exact interfaces from the plan.
- **Minimize interruptions.** The upfront Q&A exists so you can work autonomously.
- **Leave no TODOs.** Every function body gets a real implementation.
