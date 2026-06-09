---
name: ai-code-docs-user
description: "Write, update, or reorganize user documentation. Use this skill when the user says 'code user-docs', 'write user docs', 'document a feature for users', or wants end-user documentation. Do NOT use for developer docs (/ai-code-docs-dev), agent context docs (/ai-code-agent-context), or document generation (/aidoc)."
model: opus
effort: high
---

# Agent Code: User Documentation

Write and maintain end-user documentation. This skill adapts to any project by discovering doc locations and conventions at runtime, enriched with project context from `.context/README.md`.

## User Input

```text
$ARGUMENTS
```

## Context Loading

1. Read `.context/README.md` (if exists)
   - Extract from ## Code: Users, User Value (for user-facing consistency)
   - Extract from top-level: Objectives, Key Terms
   - Use Key Terms for consistent naming in user documentation

2. Check for feature awareness:
   - If documenting a feature with a `<specs_root>/<feature-name>/` folder:
     - Read README.md for feature description and requirements

## Step 0: Discover Documentation System

**ultrathink** — Framework detection must resolve ambiguous signals (multiple config files present, nested projects, monorepo doc structures). Choosing wrong means writing docs in a format the build system ignores.

Before writing anything, determine where docs live and what conventions apply.

### Mechanism 1: CLAUDE.md Context (highest signal)

Check the CLAUDE.md context for:
- **Doc paths** — directory paths for user documentation
- **Framework name** — Docusaurus, MkDocs, Sphinx, VitePress, mdBook, Jekyll, or plain Markdown
- **Conventions** — sidebar mechanism, frontmatter rules, file naming
- **Guidance file pointers** — references to style guides

If CLAUDE.md mentions a guidance file, read it before proceeding.

### Mechanism 2 & 3: Framework Detection + Heuristic Discovery

If CLAUDE.md doesn't specify doc locations, follow the detection procedure in `references/framework-detection.md`:
1. Read `.claude/skills/references/framework-detection.md`
2. Execute the Framework Detection Table (probe filesystem for each config file)
3. If no match: execute the Heuristic Fallback steps
4. **Ask the user** where user docs should go if all mechanisms fail

## Step 1: Search Existing Documentation

Search the target path for existing content on the topic:
1. **Glob for related filenames**
2. **Grep for related content** in `.md` files
3. **Check headings** for existing sections

## Step 2: Decide Action

| What you find | Action |
|---|---|
| Existing page covers this topic | **Update that page.** |
| Existing page covers a related topic | **Augment it** or **split** if > ~300 lines. |
| Multiple related pages scattered | **Consolidate first.** |
| Nothing relevant exists | **Create a new page.** |

## Step 3: File Placement

Apply framework-appropriate conventions. Use kebab-case filenames. One topic per file.

## Step 4: Write Content

### Page Structure

```markdown
# Topic Name

What this does and why it helps you. 1-3 sentences. Lead with the user's goal.

## Getting Started
Step-by-step numbered instructions.

## Configuration
Settings the user can control.

## Tips and Best Practices
How to get the most from this feature.

## Troubleshooting
**Problem:** What the user sees.
**Cause:** Why it happens.
**Solution:** What to do.

## Related
Links to complementary docs.
```

### Style Rules

- Address the user as "you". Use imperative mood for instructions.
- Lead with the user's goal, not the feature name.
- Be concise. Cut filler.
- Use Key Terms from `.context/README.md` for consistent naming.
- No marketing language ("powerful", "seamless", "robust").
- One topic per page.
- Code blocks with language identifiers.
- Explain error messages when documenting features that can fail.
- Prefer Mermaid diagrams over static images (when framework supports it).

## Step 5: Verify

- [ ] Discovered doc system before writing
- [ ] Searched existing docs first
- [ ] If consolidating: moved related pages and fixed cross-links
- [ ] Frontmatter follows framework conventions
- [ ] Content leads with the user's goal
- [ ] Instructions use numbered steps and imperative mood
- [ ] Code blocks have language identifiers
- [ ] Cross-links use relative file paths
- [ ] No marketing language or filler
- [ ] Page covers one topic only

## What This Skill Does NOT Cover

- **Developer documentation** — use `/ai-code-docs-dev`
- **Directory-level agent context docs** — use `/ai-code-agent-context`
- **Working/research documents** — ephemeral notes, plans
- **Documentation for unbuilt features** — only document what is implemented
