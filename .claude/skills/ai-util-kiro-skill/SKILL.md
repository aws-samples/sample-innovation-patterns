---
name: ai-util-kiro-skill
description: "Migrate Claude Code skills (.claude/skills/*/SKILL.md) to Kiro skills (.kiro/skills/*/SKILL.md). Use this skill when the user says 'migrate to kiro', 'convert skill to kiro', 'kiro migration', 'convert to kiro skill', 'make kiro skills', or wants to transform Claude Code skills into Kiro skill format. Also trigger when the user mentions converting skills for Kiro, porting skills, or generating .kiro/skills/ files. Do NOT use for creating new skills from scratch (/ai-util-claude-skill) or for general file conversion."
model: opus
effort: medium
---

# Kiro Skill Migration

You migrate Claude Code skills (`.claude/skills/*/SKILL.md`) to Kiro skills (`.kiro/skills/*/SKILL.md`). Both formats follow the open Agent Skills standard — the migration is primarily frontmatter cleanup, description enhancement, and cross-reference rewriting.

## User Input

```text
$ARGUMENTS
```

Consider any user input above to determine scope (specific skill, directory, or all skills).

## Background

Claude Code skills and Kiro skills both follow the **Agent Skills standard** (agentskills.io). They share the same `SKILL.md` format with YAML frontmatter. The key differences are:

| Aspect | Claude Code Skill | Kiro Skill |
|---|---|---|
| Location | `.claude/skills/<name>/SKILL.md` | `.kiro/skills/<name>/SKILL.md` |
| `name:` frontmatter | Required | Required (same) |
| `model:` frontmatter | Optional (`opus`/`sonnet`) | Not supported (add body note) |
| `description:` | Trigger/anti-trigger phrases | Clean description + activation keywords |
| `$ARGUMENTS` | Supported | Supported (confirmed working) |
| `references/` | Supported | Supported (same) |
| Cross-references | `/skill-name` | `skill-name` (plain text) |
| Invocation | `/skill-name args` | Auto-activation by description match or `/skill-name args` |

**Important**: Kiro **prompts** (`.kiro/prompts/*.md`) do NOT support `$ARGUMENTS`. Always migrate to `.kiro/skills/`, never to `.kiro/prompts/`.

## Step 1: Determine Scope

Parse the user input to determine what to migrate:

- **Specific skill**: User names a skill (e.g., "migrate ai-code-create") — migrate just that one
- **Directory of skills**: User points to a `.claude/skills/` directory — migrate all skills in it
- **All project skills**: User says "migrate all" or doesn't specify — find all `.claude/skills/*/SKILL.md` files in the project

If no skills are found, tell the user and stop.

List the skills that will be migrated and confirm with the user before proceeding.

## Step 2: Read Source Skills

For each skill to migrate, read the full `SKILL.md` file. Extract:

1. **Frontmatter fields**: `name`, `description`, `model`, and any others
2. **Body content**: Everything after the frontmatter closing `---`
3. **Cross-references**: All `/skill-name` patterns in the body (e.g., `/ai-init`, `/ai-code-create`)
4. **Model preference**: Note which skills use non-default models (e.g., `model: sonnet`)
5. **Bundled directories**: Check for `references/` and `scripts/` directories alongside the SKILL.md

## Step 3: Transform Each Skill

Apply these transformations to produce a Kiro skill file:

### 3a. Frontmatter Transformation

**Keep** `name:` — Kiro skills require it (same field as Claude Code).

**Remove** `model:` — Kiro handles model selection at the agent level, not per-skill. If a skill has `model:` that differs from the project default, add a note in the body text near the top:
"> Note: This skill produces best results with the [model name] model."

**Simplify and enhance** the `description:` field:
- Keep the first 1-2 sentences that describe what the skill does
- Strip trigger phrases ("Use this skill when the user says...")
- Strip anti-trigger phrases ("Do NOT use for...")
- Append activation keywords: "Use when [2-3 imperative/action phrases matching user intent]."
- Kiro auto-activates skills by matching user requests against descriptions, so these keywords improve activation reliability

**Remove** these fields if present (not part of the Agent Skills standard for Kiro):
- `handoffs:` — convert to body text "Next steps" guidance instead
- `argument-hint:` — Claude Code specific
- `disable-model-invocation:` — Claude Code specific
- `user-invocable:` — Claude Code specific
- `context:` — Claude Code specific (subagent execution)
- `effort:` — Claude Code specific
- `hooks:` — Claude Code specific
- `paths:` — Claude Code specific

**Example transformation:**

Before (Claude Code):
```yaml
---
name: ai-init
description: "Initialize or refine unified project context (.context/README.md). Use
  when the user says 'initialize context', 'set up context', 'start a project', 'ai init',
  'init', 'refine context', or wants to create or improve .context/ for AI-assisted
  implementation and document generation. Do NOT use for creating feature folders
  (/ai-code-create), creating document folders (/ai-doc-create), or writing agent
  context docs (/ai-code-agent-context)."
model: opus
---
```

After (Kiro):
```yaml
---
name: ai-init
description: "Initialize or refine unified project context (.context/README.md). Use
  when setting up a project, initializing context, or refining project context."
---
```

### 3b. Body Content Transformation

**ultrathink** — Cross-reference rewriting must handle multiple reference formats (slash-command mentions, prose descriptions, conditional triggers) and determine whether each reference has a Kiro equivalent, needs removal, or needs a footnote. Missing a reference produces broken skill instructions.

**Replace cross-references**: Find all `/skill-name` references in the body and replace with plain `skill-name`:
- `/ai-init` becomes `ai-init`
- `/ai-code-create "description"` becomes `ai-code-create`
- Use a pattern match for `/ai-code-`, `/ai-doc-`, and `/ai-util-` prefixes (or whatever prefixes exist in the project)
- Be careful not to replace file paths like `/src/utils/` or `/api/v1/` — only replace references that match known skill names

**Convert `handoffs:` to body text**: If the source had `handoffs:` in frontmatter, or if the skill references next steps, ensure the body's closing section includes plain-text next-step guidance. Example:
```
Next steps:
  ai-code-research <feature-name>  — research the codebase for this feature
  ai-code-plan <feature-name>      — create an implementation plan
```

**Preserve everything else**: The body content (instructions, steps, templates, examples) is platform-agnostic and should transfer unchanged. Keep `$ARGUMENTS` usage as-is — it works in Kiro skills.

### 3c. Model Preference Handling

If a skill has a `model:` field that differs from the project default:
- Add a note near the top of the body: "> Note: This skill produces best results with the [model name] model."
- This is informational — Kiro users configure model at the agent level

## Step 4: Write Output Files

1. Create the `.kiro/skills/` directory if it doesn't exist
2. For each skill, create `.kiro/skills/<skill-name>/SKILL.md`
   - `mkdir -p .kiro/skills/<skill-name>/`
   - Write the transformed content to `.kiro/skills/<skill-name>/SKILL.md`
3. If the source skill has a `references/` directory, copy it to `.kiro/skills/<skill-name>/references/`
4. If the source skill has a `scripts/` directory, copy it to `.kiro/skills/<skill-name>/scripts/`
5. Do NOT delete or modify the original Claude Code skill files

## Step 4b: Validate Migration Output

After generating each Kiro SKILL.md, verify correctness:

1. **Frontmatter check** — verify all required Kiro fields are present (`name:`, `description:`) and no Claude-only fields remain (`model:`, `effort:`, `allowed-tools:`)
2. **Cross-reference integrity** — grep the output for any remaining `/ai-` references that weren't rewritten to plain names
3. **Content preservation** — verify the skill's core logic sections are all present (compare section headings with source)
4. **No orphaned Claude-specific syntax** — check for `$ARGUMENTS`, `ultrathink`, `effort:` that should have been transformed or removed

IF validation fails: report which check failed and fix before proceeding to the next skill.

## Step 5: Report Results

Print a summary table:

```
| Source Skill | Kiro Skill | Changes |
|---|---|---|
| .claude/skills/ai-init/SKILL.md | .kiro/skills/ai-init/SKILL.md | Removed model, enhanced desc, rewrote 3 refs |
```

Then note:
- Any skills that use a non-default `model:` — the user may want to configure Kiro agents
- Cross-reference count — how many `/` to plain name replacements were made
- Any `references/` or `scripts/` directories that were copied
- Suggest the user test migrated skills in Kiro

## Edge Cases

- **Skills with no frontmatter**: Wrap the content with minimal frontmatter (`name:` derived from the directory name, `description:` derived from the first heading or paragraph)
- **Skills referencing non-skill paths**: Don't replace file paths like `/src/utils/` or `/api/v1/` — only replace references that match known skill names or the `/ai-code-` / `/ai-doc-` / `/ai-util-` prefix patterns
- **Deeply nested skill names**: Names like `ai-code-docs-user` keep the same directory name — this is valid
- **Skills with bundled scripts or references**: Copy the entire directory contents, not just SKILL.md
- **Existing Kiro skills**: If `.kiro/skills/<name>/SKILL.md` already exists, warn the user and ask whether to overwrite or skip
