---
name: ai-init
description: "Initialize or refine unified project context (.context/README.md). Use when the user says 'initialize context', 'set up context', 'start a project', 'ai init', 'init', 'refine context', 'update context', 'improve context', 'flesh out context', or wants to create or improve .context/ for AI-assisted implementation and document generation. Do NOT use for creating feature folders (/ai-code-create), creating document folders (/ai-doc-create), or writing agent context docs (/ai-code-agent-context)."
model: opus
effort: high
---

# Agent: Initialize / Refine Project Context

You manage `.context/README.md` — the unified source of truth for all AI-assisted coding and document generation in this project. You create it when it doesn't exist, and refine it when it does.

## User Input

```text
$ARGUMENTS
```

## Mode Detection

Read `.context/README.md`.

- **File does not exist** → proceed to **Create Mode** (Step C1)
- **File exists with content** → proceed to **Refine Mode** (Step R1)

---

## Create Mode

### Step C1: Seed Description

If `$ARGUMENTS` contains a project description (more than just a command name), use it as the seed description. Skip to Step C2.

Otherwise, use AskUserQuestion with one open-ended question:
- Question: "Describe your project in 2-3 sentences — what it does, who it's for, and what problem it solves."
- Header: "Project"
- Options:
  - "Web application" — full-stack or frontend web app serving end users
  - "API / backend service" — REST API, GraphQL, microservice
  - "CLI tool / library" — command-line application, SDK, or reusable package
  - "Documentation project" — primarily produces documents, not code
- multiSelect: false

Use the response (selected option + any custom text) as the seed description.

### Step C2: Adaptive Interview (max 4-5 questions)

**ultrathink** — Analyze what the seed description already reveals. Skip questions whose answers are implicit. Select 4-5 from the question bank below based on which sections would be thinnest without asking.

**Question bank — select based on gaps:**

*Product orientation (for ## Code section):*
- Who actually uses this system and what are they trying to accomplish?
- What were users doing before this existed?
- What's the one thing that makes this clearly worth using?
- What would make users stop using it?
- What does "working well" look like from the user's perspective?
- What's a stable boundary that won't change? (compliance, security, brand)

*Document orientation (for ## Documents section):*
- Who reads the documents this project produces? What do they already know?
- What tone should documents use? (formal/casual, technical/accessible — give a "sounds like" example)

Use AskUserQuestion with 4-5 questions in a single batch. Each question should have 2-4 options generated from what the description reveals, plus the ability to type custom answers.

### Step C3: Scaffold `.context/README.md`

1. Create the `.context/` directory if it doesn't exist
2. Write `.context/README.md` with this structure:

```markdown
---
output_path:
  ai-code: specs/
  ai-doc: docs/
---

# Project Context

## Project
<1-2 sentences from seed description: what this is, in plain language.>

## Objectives
<3-5 business outcomes derived from the interview. Not feature-specific — project-level goals.>

## Code

### Users
<Who uses this system and what they're trying to accomplish.>

### User Value
<What the system does for them, in their words — not technical terms.>

### Success
<What "working well" looks like from the user's perspective.>

## Documents

### Audience
<Who reads these documents and what they already know.>

### Voice
<Register + 1 "sounds like" example.>

### Principles
<Non-negotiable rules for all documents. Bullet list.>

## Key Terms
<Terms that must be used consistently across code and docs.>

## Constraints
<Stable boundaries — compliance, security, brand. Not tech patterns.>

## References
<Pointers to deeper context: CLAUDE.md files, ADRs, style guides.>
```

**Rules for writing the file:**
- Both `## Code` and `## Documents` headers are always present
- Sections populated from the interview get real content (no italic prompts)
- Sections NOT populated keep a one-line italic prompt (e.g., `*Who uses this system and what they're trying to accomplish?*`)
- No HTML comments — use italic prompts for unpopulated sections
- If the user's project is clearly code-only or docs-only, still include both headers but leave the irrelevant side with italic prompts

### Step C4: Print Integration Snippets + Next Steps

Print suggested snippets for the user to copy. Do NOT modify these files.

**For CLAUDE.md:**
```
## Project Context

Read `.context/README.md` before any implementation or document generation task.
Feature specs: `specs/<name>/` | Document folders: `docs/<name>/`
```

**For AGENTS.md:**
```
## Project Context

This project uses `.context/README.md` as unified context for AI-assisted coding and document generation.
Read it before any implementation or document generation task.
```

If no `CLAUDE.md` exists in the project root, print:
> **Tip:** Run `/ai-code-agent-context` to generate tech context (stack, patterns, build commands) in `CLAUDE.md`. The unified context file handles product orientation; `CLAUDE.md` handles tech specifics.

If no `graphify-out/graph.json` exists in the project root, print:
> **Tip:** Run `/graphify .` to build a knowledge graph of your codebase. The ai-code-* skills (research, design, plan) will query it automatically for richer architectural context.

Print next steps:
- "Your project context is ready at `.context/README.md`"
- "Paste the snippets above into your CLAUDE.md and AGENTS.md"
- "Next steps:"
- "  `/ai-init` — run again to refine the context with more detail"
- "  `/ai-code-create <description>` — create a feature folder"
- "  `/ai-doc-create <description>` — create a document folder"

---

## Refine Mode

### Step R1: Detect Gaps

**ultrathink** — Shallow gap analysis misses how thin sections compound into quality problems across all downstream skills. Analyze holistically — a thin Users section makes Objectives impossible to validate, and thin Constraints makes everything unbounded.

If the user provided specific sections or topics in `$ARGUMENTS` (e.g., `/ai-init constraints`), focus on those sections. Otherwise, auto-detect gaps across all sections.

Analyze each section:

| Section | Assessment Criteria |
|---------|-------------------|
| Project | At least 1 substantive sentence |
| Objectives | At least 3 bullet points |
| Users | Specifies who and what they're trying to do |
| User Value | Describes what the system does for users in their terms |
| Success | Defines what "working well" looks like |
| Audience | Specifies who reads docs and what they know |
| Voice | Includes register AND at least 1 example |
| Principles | At least 2 concrete principles |
| Key Terms | At least 1 defined term |
| Constraints | At least 1 stable boundary |
| References | At least 1 pointer |

Rank gaps by impact:
1. **Users / User Value** — most impactful for code pipeline; everything depends on understanding who the system serves
2. **Audience / Voice** — most impactful for doc pipeline; calibrates all document output
3. **Constraints** — boundaries for both pipelines
4. **Objectives** — what we're building toward
5. **Principles** — doc constitution
6. **Success** — outcome definition
7. **Key Terms** — consistency
8. **References** — supplementary

If the context is already comprehensive across all sections, tell the user: "Your context looks comprehensive. If you want to refine specific sections, run `/ai-init` with the section name (e.g., `/ai-init constraints`)."

Print: "Re-running `/ai-init` is for project pivots or filling gaps. Tech context (stack, patterns, testing) lives in `CLAUDE.md`. Per-feature context lives in `specs/<name>/`."

Then stop.

### Step R2: Adaptive Interview (max 4-5 questions)

Use AskUserQuestion with 4-5 questions targeting the highest-impact gaps.

Rules:
- Maximum 4-5 questions per invocation
- Skip sections that are already well-defined
- Each question should have 2-4 options generated from what the file already says
- Tailor questions to existing content — if Users says "developers," don't ask "who uses this?" — ask "what kind of developers? Frontend? Backend? What are they trying to build?"
- Only ask what genuinely affects downstream skill quality

### Step R3: Update the Context

After receiving answers, update `.context/README.md`:

1. **Preserve** all existing content — never delete what the user wrote
2. **Add** new content to the relevant sections based on answers
3. **Replace** italic prompts with real content when appropriate
4. **Maintain** the section order and heading structure
5. **Keep** YAML frontmatter unchanged unless the user specifically asked to change output paths

Use the Edit tool to make targeted changes, not Write to overwrite the whole file.

### Step R4: Report Changes

After updating, tell the user:
- Which sections were updated and what was added
- "Run `/ai-init` again to continue refining"
- "Run `/ai-code-create <description>` or `/ai-doc-create <description>` when ready to start work"
