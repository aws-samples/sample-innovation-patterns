---
name: ai-init
description: "Initialize or refine unified project context (.context/README.md). Invoke ONLY via the /ai-init slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."

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

### Step C0: Inspect the Project Before Asking Anything

Read what the repository already says about itself. Do this first — every question you can answer from these files is a question you must not ask.

1. Root `README.md` — what the project is, who it serves, what problem it solves
2. The package manifest, whichever exists: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` — name, description, and the dependency list, which reveals the domain
3. `CLAUDE.md`, if present — existing conventions and tech context

Record which file each fact came from. Step C4 reports provenance, and you cannot report what you did not track.

### Step C1: Seed Description

Sources, in priority order. Stop at the first that yields a usable description:

1. **`$ARGUMENTS`** — primary. If it carries a project description (more than just a command name), use it and go to Step C2.
2. **Step C0's inspection** — a root README or a manifest `description` field is usually enough to write the Project section. Use it, mark it inferred, and go to Step C2.
3. **Ask.** Only when both are empty, use AskUserQuestion with one open-ended question: "Describe your project in 2-3 sentences — what it does, who it's for, and what problem it solves." Header: "Project". Offer 2-3 options drafted from whatever fragments the inspection did turn up (a directory layout, a dependency set), each phrased as a candidate description the user can accept or replace by typing.

Never ask what kind of software this is. If Step C0 read a manifest or a source tree, that question is already answered; if it read nothing, the open question above covers it.

### Step C2: Fill the Gaps (0-3 questions)

**ultrathink** — Derive before you ask. Work out how much of the context the seed description plus Step C0's inspection already determines, then ask only about what genuinely remains and would change downstream output. Asking a question whose answer is already on disk trains the user to distrust the interview.

**Inference chain — follow this order:**

1. **Objectives** from the seed description. A project that "parses structured logs for on-call engineers" yields objectives about ingestion, query speed, and operator trust without anyone being asked.
2. **Constraints** from those Objectives. Objectives that name customer data imply a data-handling boundary; objectives that name a regulated domain imply an audit boundary.
3. **Repo files as supporting defaults** — the manifest, README, and `CLAUDE.md` sharpen both, and settle Key Terms and References.

**Then ask about what is left.** The ceiling is **three questions**, and the floor is **zero**:

- **Zero is the expected outcome** when `$ARGUMENTS` carried a real description and Step C0 found a populated README or manifest. Skip straight to Step C3 and say so: "Derived the context from your description, the root README, and `pyproject.toml` — no questions needed." Then let Step C4's provenance report show what was inferred.
- Ask one to three questions only when a section would otherwise be empty or wrong, not merely thin.
- Objectives is the only section worth interviewing. Constraints are inferred from it; everything else is inferred or defaulted.

**Never ask about:** voice, tone, register, or document audience — those carry a fixed default (Step C3). What kind of software this is — Step C0 answers it. Who the users are, what value they get, or what success looks like — those sections no longer exist.

When you do ask, use a single AskUserQuestion batch. Each question gets 2-4 options drafted from what you already derived, so the user is confirming a reading rather than composing from scratch.

### Step C3: Scaffold `.context/README.md`

1. Create the `.context/` directory if it doesn't exist
2. Write `.context/README.md` with this structure:

```markdown
---
output_path: docs/working
docs_path: docs/docs
---

# Project Context

## Project
<1-2 sentences from seed description: what this is, in plain language.>

## Objectives
<3-5 business outcomes derived from the seed description. Not feature-specific — project-level goals.>

## Documents

### Audience
<Who reads these documents and what they already know.>

### Voice
Professional and concise — a senior engineer explaining the work to another engineer. Direct, evidence-backed, no hedging. Measured rather than formal: the register is one of a colleague, not a specification.

### Principles
- Plain language — avoid jargon; define every technical term at first use, as a clause in the same sentence
- State the consequence — a finding says what it changes for the reader, not only what is structurally true
- Name concrete examples in prohibitions — "no marketing language ('powerful', 'seamless', 'robust')" is checkable; "avoid marketing language" is not
- Preserve analytical depth — compress the prose, never the analysis
- Restate what you point at — a reference to another part of the same document carries the substance of what it points at, so no heading or sentence is just a routing instruction; a link to another page does not have to

## Key Terms
<Terms that must be used consistently across code and docs.>

## Constraints
<Stable boundaries — compliance, security, brand. Not tech patterns. Append ` — *(inferred)*` to any bullet you derived rather than confirmed with the user.>

## References
<Pointers to deeper context: CLAUDE.md files, ADRs, style guides.>
```

**Rules for writing the file:**
- `output_path` is a single scalar naming one working root that holds every artifact folder — code features and documents alike. Write it as a plain string, never a nested mapping.
- `docs_path` names the **published** documentation tree — the directory a static-site generator serves — while `output_path` names the **working** root that holds in-progress artifact folders. Write it as a plain string. The two keys may nest: in this repo `docs_path` is `docs/docs` and `output_path` is `docs/docs/working`, so the working root sits *inside* the published tree. Any skill that walks `docs_path` must therefore exclude `output_path`. Omit `docs_path` only when the project has no published docs tree; a project with a docs site should always carry it.
- `## Documents` is always present. There is no `## Code` section: tech context lives in `CLAUDE.md`, and product orientation proved to be write-only — no skill ever read it back.
- `### Voice` and `### Principles` ship pre-filled with the wording above, verbatim. Never interview for them and never leave them as prompts. That wording is the deliverable-facing half of the standard in `.claude/skills/ai-skills-reference/voice.md`; keep the two in step if you change either.
- Sections populated from the seed description or inference get real content (no italic prompts)
- Sections genuinely unknown keep a one-line italic prompt (e.g., `*Who reads these documents and what they already know?*`)
- No HTML comments — use italic prompts for unpopulated sections
- **Mark inferred items per item, not per section.** Append the literal suffix ` — *(inferred)*` to each individual bullet you derived rather than confirmed:

  ```markdown
  ## Constraints
  - SOC 2 audit boundary — no customer data in logs
  - No eval() — *(inferred)*
  ```

  Per-item marking matters because confirming one constraint must not silently confirm the rest. Downstream skills read this suffix: `/ai-plan` warns instead of halting on an inferred constraint, and `/ai-implement` reports it instead of treating it as a hard gate. Apply the same suffix to inferred Objectives — an inferred Objective that produced an inferred Constraint is the case most worth flagging.

### Step C4: Report Provenance, Then Print Integration Snippets

**Provenance report — print this first.** The user needs to know which parts of their context are their words and which are your reading of their project. List every item you inferred, grouped by section, each with the source it came from:

```
Inferred from your description and the repo — review these:

Objectives
  - Ingest structured logs without operator configuration  (from $ARGUMENTS)
  - Keep query latency under a second on a day of logs     (from README.md "fast enough to grep interactively")

Constraints
  - No customer data in logs  (inferred from Objective 1)

Each of these carries an *(inferred)* marker in the file. /ai-plan warns rather than
stops on an inferred constraint, and /ai-implement reports rather than enforces it.
Run /ai-init again to confirm or correct any of them — removing the marker makes a
constraint binding.
```

If you inferred nothing because the user answered everything, say so in one line instead.

**Then print suggested snippets for the user to copy.** Do NOT modify these files.

**For CLAUDE.md:**
```
## Project Context

Read `.context/README.md` before any implementation or document generation task.
Artifact folders live under one working root: `docs/working/YYYY-MM-DD-<name>/` — the prefix is the folder's creation date
```

**For AGENTS.md:**
```
## Project Context

This project uses `.context/README.md` as unified context for AI-assisted coding and document generation.
Read it before any implementation or document generation task.
```

If no `CLAUDE.md` exists in the project root, print:
> **Tip:** Run `/ai-context` to generate tech context (stack, patterns, build commands) in `CLAUDE.md`. The unified context file handles product orientation; `CLAUDE.md` handles tech specifics.

If no `graphify-out/graph.json` exists in the project root, print:
> **Tip:** Run `/graphify .` to build a knowledge graph of your codebase. `/ai-research`, `/ai-architect`, and `/ai-plan` will query it automatically for richer architectural context.

Print next steps:
- "Your project context is ready at `.context/README.md`"
- "Paste the snippets above into your CLAUDE.md and AGENTS.md"
- "Next steps:"
- "  `/ai-init` — run again to refine the context with more detail"
- "  `/ai-create <description>` — create a folder for a feature or a document"

---

## Refine Mode

### Step R1: Detect Gaps

**ultrathink** — Shallow gap analysis misses how thin sections compound into quality problems across all downstream skills. Analyze holistically — thin Objectives leave every plan without a target to validate against, and thin Constraints leave everything unbounded.

If the user provided specific sections or topics in `$ARGUMENTS` (e.g., `/ai-init constraints`), focus on those sections. Otherwise, auto-detect gaps across all sections.

**Validate the `output_path` frontmatter key first.** Parse the YAML frontmatter and inspect `output_path`:

- If it is a string, use it as-is.
- If it is present but not a string — most commonly the legacy nested mapping with per-family sub-keys, which parses as a dict — print:

  WARN: "output_path in `.context/README.md` is not a string. Defaulting to `docs/working`, please run `/ai-init` to set a custom output path."

  Then offer to migrate it to the scalar form (`output_path: docs/working`, or a custom root the user names). Existing artifact folders under the old roots are not moved — say so when offering.
  Do NOT block — this is a warning, not a hard gate.
- If the key is missing entirely, report that it is absent, state that `docs/working` is in effect, and offer to write it.

**Then validate `docs_path` with the same posture.** It names the published docs tree; downstream skills walk it, so a wrong value misroutes pages.

- If it is a string, use it as-is.
- If it is present but not a string, print:

  WARN: "docs_path in `.context/README.md` is not a string. It must name the published docs root as a plain string, please run `/ai-init` to set it."

  Then offer to migrate it to the scalar form (`docs_path: docs/docs`, or the root the user names). Do NOT block — this is a warning, not a hard gate.
- If the key is missing entirely, report that it is absent, name the detected docs root as the recommended value (probe for a static-site config the way `framework-detection.md` does), and offer to write it. Do not halt when the user declines.

Analyze each section:

| Section | Assessment Criteria |
|---------|-------------------|
| Project | At least 1 substantive sentence |
| Objectives | At least 3 bullet points |
| Audience | Specifies who reads docs and what they know |
| Key Terms | At least 1 defined term |
| Constraints | At least 1 stable boundary |
| References | At least 1 pointer |
| `docs_path` (frontmatter) | Names the published docs root as a plain string |

`Voice` and `Principles` are deliberately absent from this table. They ship with a fixed default, so a populated Voice section is never a gap — assessing it would re-interview a decision the skill already made.

`## Audiences` is deliberately absent too, for a different reason: it is **optional, and this skill never interviews for it.** It is a top-level section declaring the readerships a project partitions its docs tree by, which `/ai-diataxis` reads to place a page; a project without one has a single audience, and that is the ordinary case rather than a gap. A project comes to have one at exactly two moments, neither of them here — the `/ai-diataxis-scaffold` audience question, asked once before any directory exists, and `/ai-diataxis` SURVEY offering it after a mode's contents list crosses seven items. **It is distinct from the `Audience` row above**, whose criterion is "Specifies who reads docs and what they know": that one calibrates register for `/ai-outline` and `/ai-draft` and selects no placement, while `## Audiences` selects placement and calibrates nothing. Add no frontmatter key for it and no Create Mode scaffold entry.

Rank gaps by impact:
1. **Objectives** — what everything else is validated against
2. **Constraints** — boundaries every skill respects; note that an existing bullet ending in `*(inferred)*` is a confirmation opportunity, not a gap
3. **Audience** — calibrates document output
4. **Key Terms** — consistency
5. **References** — supplementary

If the context is already comprehensive across all sections, tell the user: "Your context looks comprehensive. If you want to refine specific sections, run `/ai-init` with the section name (e.g., `/ai-init constraints`)."

Print: "Re-running `/ai-init` is for project pivots or filling gaps. Tech context (stack, patterns, testing) lives in `CLAUDE.md`. Per-folder context lives under the working root, one folder per feature or document."

Then stop.

### Step R2: Fill the Gaps (0-3 questions)

Use AskUserQuestion for the highest-impact gaps only, after deriving whatever the file and the repo already determine.

Rules:
- **Ceiling of three questions; floor of zero.** If nothing genuinely needs asking, say "Your context covers what the skills read — nothing to ask" and go to Step R3 (or stop, if there is also nothing to write).
- Infer first, exactly as Create Mode does: read the root README, the package manifest, and `CLAUDE.md`, then ask only about what remains.
- Skip sections that are already well-defined
- Each question should have 2-4 options generated from what the file already says
- Tailor questions to existing content — if Objectives names "on-call engineers," don't ask who this is for; ask which of their tasks matters most
- **Never ask about Voice, Principles, tone, register, or document audience register.** They carry a fixed default. Re-interviewing them would undo a deliberate decision every run.
- One exception worth spending a question on: an existing Constraint ending in `*(inferred)*`. Offering to confirm it converts a warning into a real gate, which is the highest-value answer available in Refine Mode.
- Only ask what genuinely affects downstream skill quality

### Step R3: Update the Context

After receiving answers, update `.context/README.md`:

1. **Preserve** all existing content — never delete what the user wrote
2. **Add** new content to the relevant sections based on answers
3. **Replace** italic prompts with real content when appropriate
4. **Maintain** the section order and heading structure
5. **Keep** YAML frontmatter unchanged unless the user specifically asked to change output paths, or Step R1 found a non-string `output_path` and the user accepted the migration to the scalar form
6. **Remove a confirmed constraint's marker.** When the user confirms a bullet that ended in `*(inferred)*`, delete just that suffix. The bullet becomes binding — `/ai-plan` will stop on it rather than warn.
7. **A legacy `## Code` section is offered for removal, never deleted silently.** Rule 1 governs: `Users`, `User Value`, and `Success` may hold the user's own words. When the file still carries them, print exactly what would be removed and ask:

   ```
   This context file has a ## Code section (Users, User Value, Success). No skill reads
   those three sections — /ai-init no longer scaffolds them. Remove them?

     Users:      "Developers who use AI-assisted development tools..."
     User Value: "Every AI interaction reads your project's patterns..."
     Success:    "A developer runs /ai-plan and gets a plan that respects..."

     A) Remove all three and the ## Code heading
     B) Keep them — they are useful to me as a human reader
   ```

   Never remove them without an answer. Content nothing reads is still content someone wrote.

Use the Edit tool to make targeted changes, not Write to overwrite the whole file.

### Step R4: Report Changes

After updating, tell the user:
- Which sections were updated and what was added
- Whether `output_path` was migrated to the scalar form, and that existing artifact folders were not relocated
- "Run `/ai-init` again to continue refining"
- "Run `/ai-create <description>` when ready to start work"
