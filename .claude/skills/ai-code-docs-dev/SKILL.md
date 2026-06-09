---
name: ai-code-docs-dev
description: "Write, update, or consolidate developer documentation. Use this skill when the user says 'code dev-docs', 'write dev docs', 'developer documentation', or wants technical docs aimed at contributors. Do NOT use for user docs (/ai-code-docs-user), agent context docs (/ai-code-agent-context), or document generation (/aidoc)."
model: opus
effort: high
---

# Agent Code: Developer Documentation

Write and maintain developer-facing documentation. This skill adapts to any project by discovering doc locations and conventions at runtime, enriched with project context from `.context/README.md`.

## User Input

```text
$ARGUMENTS
```

## Context Loading

1. Read `.context/README.md` (if exists)
   - Extract from top-level: Objectives, Constraints, Key Terms for project vocabulary
   - Use Key Terms for consistent naming throughout documentation
   - For tech context (architecture, patterns, stack), read `CLAUDE.md` if present

2. Check for feature awareness:
   - If documenting a feature with a `<specs_root>/<feature-name>/` folder:
     - Read README.md for feature identity
     - Read as-built.md (if exists) for implementation context

## Step 0: Discover Documentation System

**ultrathink** — Framework detection must resolve ambiguous signals (multiple config files present, nested projects, monorepo doc structures). Choosing wrong means writing docs in a format the build system ignores.

Before writing anything, determine where docs live and what conventions apply.

### Mechanism 1: CLAUDE.md Context (highest signal)

Check the CLAUDE.md context for:
- **Doc paths** — directory paths for developer documentation
- **Framework name** — Docusaurus, MkDocs, Sphinx, VitePress, mdBook, Jekyll, or plain Markdown
- **Conventions** — sidebar mechanism, frontmatter rules, file naming
- **Guidance file pointers** — references to style guides or writing conventions

If CLAUDE.md mentions a guidance file, read it before proceeding.

### Mechanism 2 & 3: Framework Detection + Heuristic Discovery

If CLAUDE.md doesn't specify doc locations, follow the detection procedure in `references/framework-detection.md`:
1. Read `.claude/skills/references/framework-detection.md`
2. Execute the Framework Detection Table (probe filesystem for each config file)
3. If no match: execute the Heuristic Fallback steps
4. **Ask the user** where developer docs should go if all mechanisms fail

## Step 1: Search Existing Documentation

Search the target path for existing content on the topic:
1. **Glob for related filenames**
2. **Grep for related content** in `.md` files
3. **Check headings** for existing sections

## Step 2: Decide Action

| What you find | Action |
|---|---|
| Existing doc covers this topic | **Update that doc.** |
| Existing doc covers a parent/sibling topic | **Add a section to that doc.** |
| 2+ standalone docs share a theme | **Consolidate into a subdirectory.** |
| Nothing related exists | **Create a new page.** |

## Step 3: File Placement

Apply framework-appropriate conventions. Use kebab-case filenames. One topic per document.

## Step 4: Write Content

### Document Structure

```markdown
# Topic Name

Brief orientation — what this is and why it exists. 1-3 sentences.

## How It Works
Implementation explanation with code snippets where helpful.
Reference source files by repo-relative path.

## Usage
How to use this from a developer perspective. Concrete examples.

## Extending / Maintaining
Key files, patterns, gotchas, dependencies.
Call out non-obvious coupling and ripple effects.

## Known Issues
Current limitations and workarounds. Omit if none exist.

## References
Internal cross-links (relative file paths) and external resources.
```

### Style Rules

- **Audience:** Developers contributing to the project. Assume language familiarity.
- **Tone:** Direct, technical, concise. No filler.
- **Voice:** Second person ("you") or imperative. No first person.
- **Terminology:** Use Key Terms from `.context/README.md` for consistent naming.
- **Code snippets:** Fenced blocks with language identifiers. Keep to 5-20 lines.
- **Diagrams:** Prefer Mermaid over static images.
- **No fluff:** No introductions restating the title. No concluding summaries.

## Step 5: Verify

- [ ] Discovered doc system before writing
- [ ] Searched existing docs first
- [ ] If consolidating: moved related pages, updated all cross-links
- [ ] Frontmatter follows framework conventions
- [ ] Document follows the section structure
- [ ] Code snippets have language identifiers and reference source files
- [ ] Cross-links use relative file paths
- [ ] No empty or placeholder sections
- [ ] One topic per document
- [ ] No content duplicated from user docs — cross-link instead

## What This Skill Does NOT Cover

- **User documentation** — use `/ai-code-docs-user`
- **Directory-level agent context docs** — use `/ai-code-agent-context`
- **Working/research documents** — ephemeral notes, plans
- **Documentation for unbuilt features** — only document what is implemented
