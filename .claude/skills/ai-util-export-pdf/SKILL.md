---
name: ai-util-export-pdf
description: "Export a markdown file to a branded PDF. Use when the user says 'export to pdf', 'aiutil pdf', 'render to pdf', 'make a pdf', 'convert markdown to pdf', 'branded pdf', 'markdown to pdf', '/ai-util-export-pdf', or wants to produce a styled PDF from a markdown file."
effort: medium
---

# Agent Docs: Export to Branded PDF

You convert a markdown file into a professionally styled PDF using a bundled PEP 723 renderer script. The PDF features a branded cover page, navy/orange color scheme, table of contents, and consistent typography.

## User Input

```text
$ARGUMENTS
```

Expected: a path to a `.md` file (absolute or relative to the working directory).

## Step 1: Validate Input File

1. Resolve the file path from `$ARGUMENTS`
   - If no argument provided: ask the user for the path to their markdown file
   - If path doesn't end in `.md`: ask if they meant a different file
2. Check the file exists using `ls`
   - If not found: STOP — tell the user the file was not found

## Step 2: Read Frontmatter and Check Required Fields

1. Read the markdown file
2. Look for a YAML frontmatter block at the top (between `---` delimiters)
3. Check for these **required** fields:
   - `title` — OR check if there is exactly one `# H1 Heading` in the body (if so, it becomes the title automatically via heading-demotion)
   - `organization`
   - `client`
   - `classification`
4. Note which required fields are missing

## Step 3: Prompt for Missing Required Fields

For each missing required field from Step 2, use AskUserQuestion to gather the value:

- **title** (only if no frontmatter `title:` AND the document does NOT have exactly one H1): "What is the document title?"
- **organization**: "What is the organization name?" — provide options including "AWS Generative AI Innovation Center" (Recommended) as the first option
- **client**: "What is the client name? (e.g., 'Acme Corp')"
- **classification**: "What is the document classification? (e.g., 'Confidential', 'Internal', 'Public')"

If ALL required fields are present in frontmatter (or title is covered by a single H1): skip prompting entirely.

## Step 4: Check Environment

1. Check that `uv` is available:
   ```bash
   which uv
   ```
   - If not found: STOP — print: "This skill requires `uv`. Install it with: `curl -LsSf https://astral.sh/uv/install.sh | sh`"

2. Check for optional `mmdc` (Mermaid CLI):
   ```bash
   which mmdc
   ```
   - If not found: note (do NOT stop): "Note: Mermaid diagrams will render as code blocks. Install `npm install -g @mermaid-js/mermaid-cli` to render them as images."

## Step 5: Invoke Renderer

1. Print: "Installing PDF renderer dependencies (first time only)..." before the first invocation.

2. Determine the script path — it is the `render_template.py` sibling file in this skill's directory:
   ```
   .claude/skills/ai-util-export-pdf/render_template.py
   ```
   Resolve relative to the project root (the repo root where `.claude/` lives).

3. Build the command. Start with:
   ```bash
   uv run --script <script_path> "<input_file>"
   ```

4. Append CLI overrides for any values gathered in Step 3:
   - `--title "VALUE"` (if title was prompted)
   - `--organization "VALUE"` (if organization was prompted)
   - `--client "VALUE"` (if client was prompted)
   - `--classification "VALUE"` (if classification was prompted)

5. Run the command.

## Step 6: Report Result

After successful execution:

1. The script prints `Wrote <path> (<size> KB)` — relay this to the user
2. Confirm: "PDF exported to `<output_path>`"
3. Suggest: "Open the PDF to verify formatting. Re-run `/ai-util-export-pdf <path>` after editing the markdown."

If the command fails:
1. Read the error output
2. Common issues:
   - Missing dependencies on first run → usually resolves on retry
   - Invalid markdown syntax → report the specific error
   - Missing font or image file → report which file was not found

## Supported Markdown Features

The renderer supports:

| Feature | Syntax |
|---------|--------|
| Headings H1-H3 | `#`, `##`, `###` |
| H3 accent (orange) | `###! Heading` |
| Bold/italic/code | `**b**`, `*i*`, `` `code` `` |
| Bullet lists | `- item` (2 levels) |
| Tables | `\| h1 \| h2 \|` |
| Custom table widths | `<!-- widths: 30% 70% -->` |
| Code blocks | ` ```lang ` |
| Mermaid diagrams | ` ```mermaid ` (requires mmdc) |
| Admonitions | `> [!INFO]`, `> [!WARNING]`, `> [!CRITICAL]` |
| Page breaks | `\pagebreak` or `<!-- pagebreak -->` |
| Horizontal rules | `---` |
| Cover page | YAML frontmatter |
| Table of Contents | Auto-generated (H1 level) |

## Frontmatter Reference

```yaml
---
organization: AWS Generative AI Innovation Center
client: Acme Corp
title: Document Title
subtitle: Optional Subtitle
classification: Confidential
industry: FinTech
date: 2026-05-18
logo: ./path/to/logo.png
---
```

- **Required** (prompted if missing): `title`, `organization`, `client`, `classification`
- **Optional** (defaults silently): `subtitle` (empty), `industry` (empty), `date` (today), `logo` (none)
