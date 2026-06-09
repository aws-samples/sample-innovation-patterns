# Manifest Update Reference

Shared instructions for updating the specs/docs manifest README after skill execution.

## Algorithm

After updating the feature/document status, update the manifest README:

1. Determine the output directory:
   - For code skills: `<output_path.ai-code>` (e.g., `docs/docs/working/specs/`)
   - For doc skills: `<output_path.ai-doc>` (e.g., `docs/docs/working/docs/`)

2. Read the existing manifest at `<output_dir>/README.md`
   - If it does not exist, create it with the template below

3. Scan the current feature/document folder's README.md:
   - Extract `title` from frontmatter (or H1 heading)
   - Extract description from the `## Description` section (first sentence only)
   - Determine state from the `## Status` checkboxes — use the LAST checked item:
     - Code: Research → Design → Plan → Implement → Test
     - Docs: Research → Outline → Draft

4. Find the row for this folder in the manifest table and update it
   - If no row exists, append a new row (maintain alphabetical order)
   - If the row exists and nothing changed, leave it alone

5. Update the "Last updated" date in the blockquote to today's date

6. Write the updated manifest back with the Edit tool (preserve all other rows unchanged)

## Manifest Template

```markdown
# [Specs|Docs] Manifest

> Auto-updated by ai-skills pipeline. Last updated: <YYYY-MM-DD>

| Folder | State | Description |
|--------|-------|-------------|
```

## State Emoji Key

### Code Skills

| Emoji | State | Condition |
|-------|-------|-----------|
| 🆕 | Created | Has README only (no status checked) |
| 🔬 | Research | `[x] Research` is last checked |
| 📐 | Design | `[x] Design` is last checked |
| 📋 | Plan | `[x] Plan` is last checked |
| 🏗️ | Implement | `[x] Implement` is last checked |
| ✅ | Complete | `[x] Test` is checked |

### Doc Skills

| Emoji | State | Condition |
|-------|-------|-----------|
| 🆕 | Created | Has README only (no status checked) |
| 🔬 | Research | `[x] Research` is last checked |
| 📝 | Outline | `[x] Outline` is last checked |
| ✏️ | Draft | `[x] Draft` is last checked |
| ✅ | Complete | All items checked |

## Row Format

```
| [<folder-name>](<folder-name>/) | <emoji> <State> | <first sentence of Description> |
```
