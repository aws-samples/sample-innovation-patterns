---
name: ai-doc-draft
description: "Write a full document draft for AI document generation, incorporating research and outline if available. Use this skill when the user says 'aidoc draft', 'write the document', 'draft my doc', 'write the draft', 'generate the document', or wants to produce the actual document content. Also trigger when the user says 'write it', 'draft it', or 'create the final document' in the context of an aidoc document project. Do NOT use for general writing tasks (/writer), research (/ai-doc-research), outlines (/ai-doc-outline), or writing that isn't part of an aidoc document project."
model: opus
effort: xhigh
---

# Agent Docs: Draft

You write a full document draft that respects the project brief's constraints and incorporates available research and outline. The draft should read like a real document — not a template, skeleton, or placeholder.

## User Input

```text
$ARGUMENTS
```

Expected: `[document-name]` — which document folder to write the draft for.

## Step 1: Read the Brief

Read `.context/README.md` from the project root.

- If not found: warn and suggest `/ai-init`. Continue if the user insists, but note that the draft won't be constrained by project context.
- If found: parse `output_path.ai-doc` from frontmatter. Load the COMPLETE brief:
  - **Project**: What this project is about
  - **Objectives**: What the document should achieve
  - **Audience**: Who reads it, what they know, what they need to learn
  - **Voice & Tone**: How it should sound — match this register throughout
  - **Principles**: Non-negotiable rules — the document MUST comply with every principle
  - **Key Terms**: Use these exactly as defined, consistently throughout
  - **Constraints**: Hard limits — never cross these boundaries
  - **References**: Read every referenced document for additional context

The brief's Principles are the constitution. Every principle is non-negotiable. If a principle says "cite all sources," every factual claim in the draft must have a citation. If it says "plain language," no jargon without definition.

## Step 2: Resolve the Document Folder

1. If `$ARGUMENTS` specifies a document name → use `<output_path.ai-doc>/<name>/`
2. If one folder in `<output_path.ai-doc>/` → use it
3. If multiple folders → list and ask
4. If no folders → suggest `/ai-doc-create`

## Step 3: Read the README.md

Read `<doc-folder>/README.md` for document-specific context:
- **Title**: use this as the document's H1
- **Description**: the document's identity and purpose
- **Scope**: what this document covers and doesn't — stay within bounds
- **Audience**: the specific audience for this document (may be narrower than the brief's audience)

## Step 4: Read Existing Artifacts

Read these files from the document folder (all optional):

1. **`outline.md`** — if it exists, this is the primary structure guide. Follow its heading hierarchy and section guidance closely. Pay attention to the Objective Coverage Map and Validation Notes.
2. **`research.md`** — if it exists, incorporate findings, data, and sources into the draft. Use the Sources section for citations. Note any Gaps & Caveats — do not present thin evidence as definitive.

Priority:
- If both exist: follow the outline structure, fill in with research content
- If only outline exists: follow the outline, use brief context for content
- If only research exists: organize research into a logical structure for the audience
- If neither exists: create a logical structure based on the brief's objectives and audience

## Step 5: Write the Draft

**ultrathink** — Synthesizing brief constraints, outline structure, and research findings into a coherent writing plan requires resolving tensions between principles (e.g., "cite all sources" + "plain language" requires careful citation style) before writing begins. Plan the synthesis deliberately.

Write a complete document that:

1. **Follows the outline** (if available) — use its heading hierarchy as the document's backbone. The guidance notes under each heading tell you what to write.

2. **Incorporates research** (if available) — weave findings, data, quotes, and analysis from `research.md` into the appropriate sections. Include source citations.

3. **Respects the brief** — this is non-negotiable:
   - Write at the audience's level
   - Use the specified voice and tone throughout
   - Comply with every principle
   - Use key terms consistently
   - Stay within constraints
   - Serve the stated objectives

4. **Reads like a real document** — not a template or skeleton:
   - Include substantive content, not "[insert content here]" placeholders
   - Write complete paragraphs with real arguments, data, and analysis
   - Include transitions between sections
   - End with a section appropriate to the document type (conclusion, next steps, recommendations, call to action)

5. **Includes only frontmatter** — the draft starts with a YAML frontmatter block (`title: "Draft: <Document Title>"`) followed by the document title (H1). No other metadata headers ("Document:", "Brief:", "Date:"). The document body should read like a document the audience would actually receive.

## Step 5b: Verify Principle Compliance

Before writing to file, spot-check the draft against each brief principle:

FOR each principle in the brief's Principles section:
1. Select 3-5 representative sentences from different sections of the draft
2. Assess: does each sentence comply with this principle?
3. IF any sentence violates a principle:
   - Identify the violation
   - Revise the sentence to comply
   - Check surrounding sentences for the same pattern

This is not a full audit — it's a targeted spot-check to catch systematic drift from the brief's constitution. The most common failure mode is gradual tone/style drift in later sections as the model loses focus on the constraints.

## Step 6: Write to File

Write the draft to `<doc-folder>/draft.md`.

If a `draft.md` already exists, overwrite it. Drafts are regenerated, not appended. Tell the user you're replacing the existing draft.

## Step 7: Update Status and Confirm

Update `<doc-folder>/README.md` Status: check `[x] Draft`.

Tell the user:
- "Draft written to `<doc-folder>/draft.md`"
- "Review the draft and edit as needed"
- "To regenerate with different direction: edit the outline or brief, then run `/ai-doc-draft <name>` again"
- "Export: `/ai-util-export-docx` for Word, `/ai-util-export-pdf` for PDF"

## Manifest Update

After updating status, update the docs manifest at `<docs_root>/README.md`:

1. Read `<docs_root>/README.md` (create from template if missing — see `references/manifest-update.md`)
2. Read this document's README.md — extract title, first sentence of Description, and last checked Status item
3. Find or append the row for this folder in the table (maintain alphabetical order)
4. Determine state emoji: 🆕 (README only) → 🔬 (Research) → 📝 (Outline) → ✏️ (Draft) → ✅ (Complete)
5. Update the row: `| [<folder>](<folder>/) | <emoji> <State> | <description> |`
6. Update the "Last updated" date in the blockquote
7. Write back with the Edit tool (preserve all other rows unchanged)
