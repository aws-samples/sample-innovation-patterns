---
name: ai-draft
description: "Write a full document draft, incorporating research and outline if available. Invoke ONLY via the /ai-draft slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."

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
- If found: parse `output_path` from frontmatter (default: `docs/working`) and use it as `<output_root>`. Load the COMPLETE brief:
  - If `output_path` is not a string, WARN: "output_path in `.context/README.md` is not a string. Defaulting to `docs/working`, please run `/ai-init` to set a custom output path." Do NOT block — this is a warning, not a hard gate.
  - **Project**: What this project is about
  - **Objectives**: What the document should achieve
  - **Audience**: Who reads it, what they know, what they need to learn
  - **Voice & Tone**: How it should sound — match this register throughout
  - **Principles**: Non-negotiable rules — the document MUST comply with every principle
  - **Key Terms**: Use these exactly as defined, consistently throughout
  - **Constraints**: Hard limits — never cross these boundaries
  - **References**: Read every referenced document for additional context

The brief's Principles are the constitution. Every principle is non-negotiable. If a principle says "formal tone," the draft must not lapse into casual phrasing. If it says "plain language," no jargon without definition.

**Voice standard, on top of the brief.** Read `ai-skills-reference/voice.md` before writing. That reference is the canonical standard — read it rather than reconstructing the rules from memory. Three standards apply here, and none displaces another:

1. The **core rules** always apply — all six of them, as the standard states them, not a remembered subset.
2. `draft.md` is a deliverable, so the **deliverable overlay** also applies — third-person register, bibliographic citation where the brief calls for it.
3. The **brief's Principles** remain the constitution and win on any conflict, because they are what this specific document was commissioned against.

Where the overlay and the brief agree, they reinforce. Where the brief is stricter, the brief governs.

**Citation mode.** By default, citation behavior follows the brief's Principles/Constraints: cite only if the brief calls for it. An explicit citation instruction in the invocation (e.g. "cite everything", "no citations", "minimal citations") overrides that default. When citations are required, prefer inline prose links over bare `[n]` markers, and do not carry researcher-facing source-reliability grades from `research.md` into the delivered draft.

## Step 2: Resolve the Document Folder

1. If `$ARGUMENTS` specifies a document name and `<output_root>/<name>/` exists → use it
2. If `$ARGUMENTS` specifies a document name with no exact match → collect entries in `<output_root>/` matching `????-??-??-<name>` exactly (an 11-character `YYYY-MM-DD-` prefix followed by the typed name and nothing else)
   - Exactly one match: use it. Tell the user which dated folder resolved.
   - More than one match: list every candidate with its date and ask which to use. Never silently pick one, and never pick the newest by default.
   - No match: suggest `/ai-create <name>` — this skill does not create folders.
3. If exactly one folder exists in `<output_root>/` → use it
4. If more than one folder exists → list them and ask which one. One root holds every folder — code and documents alike — so do not silently bind to an arbitrary folder.
5. If no folders → suggest `/ai-create`

A document folder created by `/ai-create` carries a `YYYY-MM-DD-` creation-date prefix, so the name a user types is usually the undated portion. Step 2 is what binds the short name to the dated folder — and to the `outline.md` and `research.md` already sitting in it. Never re-date a folder — the prefix records creation, not the current run.

## Step 3: Read the README.md

Read `<doc-folder>/README.md` for document-specific context:
- **Title**: use this as the document's H1
- **Description**: the document's identity and purpose
- **Scope**: what this document covers and doesn't — stay within bounds
- **Audience**: the specific audience for this document (may be narrower than the brief's audience)

## Step 4: Read Existing Artifacts

Read these files from the document folder (all optional):

1. **`outline.md`** — if it exists, this is the primary structure guide. Follow its heading hierarchy and section guidance closely. Pay attention to the Objective Coverage Map and Validation Notes.
2. **`research.md`** — if it exists, incorporate findings, data, and provenance into the draft. Carry provenance into the draft only to the extent the brief's Principles or Constraints require, or the caller requested (see Citation mode below). Note any Gaps & Caveats — do not present thin evidence as definitive.

Priority:
- If both exist: follow the outline structure, fill in with research content
- If only outline exists: follow the outline, use brief context for content
- If only research exists: organize research into a logical structure for the audience
- If neither exists: create a logical structure based on the brief's objectives and audience

## Step 5: Write the Draft

**ultrathink** — Synthesizing brief constraints, outline structure, and research findings into a coherent writing plan requires resolving tensions between principles (e.g., "plain language" + "formal tone" requires careful register control) before writing begins. Plan the synthesis deliberately.

Write a complete document that:

1. **Follows the outline** (if available) — use its heading hierarchy as the document's backbone. The guidance notes under each heading tell you what to write.

2. **Incorporates research** (if available) — weave findings, data, quotes, and analysis from `research.md` into the appropriate sections.

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

**Also run the voice pre-write check** when the draft exceeds roughly 300 lines: sample 3-5 sentences from the final third and confirm each term is defined where it first appears, each finding carries its consequence, and each reference to another part of the draft carries that part's substance. See the Pre-Write Verification step in `ai-skills-reference/voice.md`. Same failure mode as above, different axis — fix the sentence and check its neighbours, since drift is systematic rather than isolated.

## Step 6: Write to File

Write the draft to `<doc-folder>/draft.md`.

If a `draft.md` already exists, overwrite it. Drafts are regenerated, not appended. Tell the user you're replacing the existing draft.

## Step 7: Update Status and Confirm

Update `<doc-folder>/README.md` Status: check `[x] In progress` (the 3-item ladder is Research / In progress / Complete; `Complete` is checked by a human, never by a skill).

Tell the user:
- "Draft written to `<doc-folder>/draft.md`"
- "Review the draft and edit as needed"
- "To regenerate with different direction: edit the outline or brief, then run `/ai-draft <name>` again"
- "Export: `/ai-util-export-docx` for Word, `/ai-util-export-pdf` for PDF"

## Manifest Update

After updating status, update the working manifest at `<output_root>/README.md`:

1. Read `<output_root>/README.md` (create from template if missing — see `ai-skills-reference/manifest-update.md`)
2. Read this document's README.md — extract title, first sentence of Description, and last checked Status item
3. Find or append the row for this folder in the table (maintain alphabetical order — for `YYYY-MM-DD-` names this is also chronological order, oldest first; undated legacy rows sort after dated ones because digits precede letters in ASCII)
4. Determine state emoji from the 4-state ladder in `ai-skills-reference/manifest-update.md`: 🆕 (README only) → 🔬 (Research) → 🛠️ (In progress) → ✅ (Complete)
5. Update the row: `| [<folder>](<folder>/) | <emoji> <State> | <description> |`
6. Update the "Last updated" date in the blockquote
7. Write back with the Edit tool (preserve all other rows unchanged)
