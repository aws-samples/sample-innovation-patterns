---
name: ai-doc-create
description: "Create a new document folder with a README.md identity document for AI document generation. Use this skill when the user says 'create a document', 'new document', 'aidoc create', 'start a new doc', 'add a document', 'create doc folder', or wants to set up a new document workspace within their aidoc project. Also trigger when the user provides a document description and wants a folder created for it. Do NOT use for initializing or refining the project brief (/ai-init) or generating any content (research, outline, draft)."
model: opus
effort: high
---

# Agent Docs: Create Document

You create a new document folder and write a README.md identity document that establishes the document's metadata, scope, and context for all subsequent skills.

## User Input

```text
$ARGUMENTS
```

Expected format: `[document-name] <description>`

The first token may be a folder name. If the first word looks like a kebab-case identifier (lowercase, hyphens, no spaces), treat it as the document name and use the rest as the description. Otherwise, treat the entire input as the description and derive the folder name in Step 4.

## Step 1: Read the Brief

Read `.context/README.md` from the project root.

- If the file does not exist:
  - Tell the user: "No brief found at `.context/README.md`. Run `/ai-init` first to set up your project context."
  - Stop. Do not create the folder without a brief.
- If the file exists: parse the YAML frontmatter and extract `output_path.ai-doc` (default: `docs/`). Load the full brief — you'll use it to enrich the README.

## Step 2: Get the Document Description

If `$ARGUMENTS` is empty or contains only whitespace:
- Ask the user: "What document do you want to create? Describe it in a sentence or two."
- Wait for their response.

If a document name was extracted from the first token (see format above), use the remaining text as the description. Otherwise, use the entire input as the description.

## Step 3: Analyze the Description

**Use extended thinking for this step.** The README you produce becomes the identity card that every downstream skill reads — getting the scope, audience, and purpose right here prevents compounding errors in research, outlining, and drafting.

Before deriving a name, analyze the description to extract:
- **Subject**: What is this document about?
- **Purpose**: Why is it being created? (inform, persuade, educate, report)
- **Document type**: Report, guide, proposal, analysis, reference, etc.
- **Audience signals**: Does the description mention or imply a specific audience?
- **Scope signals**: Any explicit inclusions or exclusions?

This analysis feeds both the folder name and the README content. Inspired by speckit.specify's "extract key concepts: actors, actions, data, constraints" — adapted for document production.

## Step 4: Derive the Folder Name

From the analysis, extract the 2-5 most meaningful keywords:

1. Convert to lowercase
2. Remove articles and filler prepositions unless meaningful
3. Replace spaces/underscores with hyphens
4. Remove non-alphanumeric characters (except hyphens)
5. Collapse consecutive hyphens
6. Truncate to 50 characters at a word boundary

Examples:
- "Q1 2026 Quarterly Report for the Board" → `q1-2026-quarterly-report`
- "Product Roadmap" → `product-roadmap`
- "The Getting Started Guide" → `getting-started-guide`
- "Competitive Analysis of Cloud Storage Providers" → `cloud-storage-competitive-analysis`

## Step 5: Check for Conflicts

Check if `<output_path.ai-doc>/<derived-name>/` already exists.

If it exists, use AskUserQuestion:
- "Use existing folder" — proceed (do not overwrite README.md)
- "Choose a different name" — ask for a new name

## Step 6: Create Folder and README.md

1. `mkdir -p <output_path.ai-doc>/<derived-name>/`
2. Write `<output_path.ai-doc>/<derived-name>/README.md`:

```
---
title: <doc-name>
---

# <Document Title>

## Description
<1-2 sentences: what this document is and why it's being created.
 Derived from description, enriched with brief context.>

## Scope
<What this document covers and does not cover.
 Inferred from description and document type.
 Specific enough to guide research and outlining.>

## Audience
<Who reads THIS document. Narrowed from the brief's Audience.>

## Status
- [ ] Research
- [ ] Outline
- [ ] Draft
- [ ] Review
```

Write real content, not placeholders. The README is the document's identity card — every subsequent skill reads it.

## Step 7: Confirm and Guide

Tell the user:
```
Created document: <output_path.ai-doc>/<derived-name>/
Identity:  <output_path.ai-doc>/<derived-name>/README.md

Next steps:
  /ai-doc-research <derived-name> <topic>  — research a topic for this document
  /ai-doc-outline <derived-name>           — create a structured outline
  /ai-doc-draft <derived-name>             — write the full document
```

## Step 8: Manifest Update

After creating the document folder, update the docs manifest at `<docs_root>/README.md`:

1. Read `<docs_root>/README.md` (create from template if missing — see `references/manifest-update.md`)
2. Read the new document's README.md — extract title, first sentence of Description, and last checked Status item
3. Append a new row to the table (maintain alphabetical order)
4. Determine state emoji: 🆕 (README only) → 🔬 (Research) → 📝 (Outline) → ✏️ (Draft) → ✅ (Complete)
5. Add the row: `| [<folder>](<folder>/) | <emoji> <State> | <description> |`
6. Update the "Last updated" date in the blockquote
7. Write back with the Edit tool (preserve all other rows unchanged)
