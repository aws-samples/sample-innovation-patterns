---
name: ai-doc-outline
description: "Create a structured document outline with heading hierarchy, section guidance, and constitution-validated coverage. Use this skill when the user says 'aidoc outline', 'create an outline', 'outline the document', 'outline my doc', 'structure the document', or wants a heading-level plan before drafting. Also trigger when the user says 'what should the document cover' or 'organize the document'. Do NOT use for writing the actual document (/ai-doc-draft), researching topics (/ai-doc-research), or general outlining unrelated to an aidoc document project."
model: opus
effort: xhigh
---

# Agent Docs: Outline

You create a structured document outline with heading hierarchy and guidance for each section. The outline is constitution-checked against the brief's principles and validated for objective coverage before being written. It serves as a blueprint for drafting.

## User Input

```text
$ARGUMENTS
```

Expected: `[document-name]` — which document folder to write the outline for.

## Step 1: Read the Brief

Read `.context/README.md` from the project root.

- If not found: warn and suggest `/ai-init`. Continue if the user wants.
- If found: parse `output_path.ai-doc` from frontmatter. Load the COMPLETE brief:
  - **Project**: context for the document
  - **Objectives**: what the document must achieve — these drive coverage validation
  - **Audience**: who reads it, what they know — this drives section ordering and depth
  - **Voice & Tone**: register for section guidance notes
  - **Principles**: non-negotiable rules — these form the **constitution** for validation
  - **Key Terms**: must appear in the outline where relevant
  - **Constraints**: hard limits — the outline must respect these
  - **References**: read every referenced document for additional context

## Step 2: Resolve the Document Folder

1. If `$ARGUMENTS` specifies a document name → use `<output_path.ai-doc>/<name>/`
2. If one folder in `<output_path.ai-doc>/` → use it
3. If multiple folders → list and ask
4. If no folders → suggest `/ai-doc-create`

## Step 3: Read the README.md

Read `<doc-folder>/README.md` for document-specific context:
- **Title**: the document's human-readable title
- **Description**: what this specific document is about
- **Scope**: what it covers and doesn't
- **Audience**: narrowed from the brief's audience to this document

This is the document's identity. The outline must serve THIS document's scope and audience, not just the general brief.

## Step 4: Read Research Artifacts

Check for `<doc-folder>/research.md`:
- If it exists: read it. The outline should organize and reflect the research findings. Pay special attention to the **Coverage Assessment** and **Gaps & Caveats** sections — these tell you where evidence is strong and where it's thin.
- If it doesn't exist: base the outline on the brief context alone. This is fine — research is optional.

## Step 5: Constitution Check (Gate)

**ultrathink** — A missed principle becomes an unconstrained area in the draft. Each principle must be evaluated against the planned structure — think through how the outline can structurally enforce each one, and identify any that can only be handled at draft time.

Before generating the outline, validate that you have enough context to produce a useful structure. This is a **gate** — if it fails, stop and tell the user what's missing.

**Extract the constitution** from the brief's Principles section. Each principle is a non-negotiable rule.

**Check each principle against the planned outline approach:**

For each principle, ask: "Can I design an outline structure that ensures the drafter will comply with this principle?"

Examples:
- Principle: "Cite all sources" → outline must include a Sources/References section and guidance to cite within body sections
- Principle: "Plain language" → section guidance must note the register; no jargon-heavy section titles
- Principle: "Include code examples" → at least one section must be designated for examples
- Principle: "Accessible to beginners" → outline must start with foundational concepts before advanced topics

**If a principle cannot be addressed** by the outline structure:
- WARN the user: "Principle '<X>' cannot be structurally enforced in the outline. The drafter will need to handle this at write time."
- Do NOT block — this is a warning, not a hard gate.

**If essential context is missing** (no brief, no README.md, no idea what the document is about):
- STOP. Tell the user what's missing and suggest the appropriate skill.

## Step 6: Generate the Outline

### 6a: Build Objective-to-Section Coverage Map

Before writing sections, map every objective from the brief to at least one planned section:

| Objective | Planned Section(s) | Coverage |
|-----------|-------------------|----------|
| <Objective 1 from brief> | <Section name(s)> | Full / Partial / None |
| <Objective 2 from brief> | <Section name(s)> | Full / Partial / None |

**Gate**: If any objective has "None" coverage, add a section to address it or explain why it's out of scope for this document (referencing README.md's Scope).

### 6b: Generate Section Hierarchy

Create a heading hierarchy that:
- Follows a logical flow appropriate for the audience (from brief + README.md)
- Organizes research findings (if available) into coherent sections
- Ensures every brief objective maps to at least one section
- Uses H1 for the document title, H2 for major sections, H3 for subsections
- Uses H4 only when genuinely needed for complex sections

Under each heading, include **2-4 bullet points of guidance**:
- What this section should cover
- Key points to include (drawn from research if available)
- Which brief objective(s) this section serves
- Approximate scope: brief paragraph? detailed analysis? data table? bullet list?
- Any constitution principle that specifically applies to this section

The outline is prescriptive enough to be useful as a drafting blueprint but flexible enough to allow creative decisions during drafting.

### 6c: Outline Format

```
---
title: "Outline: <Document Title>"
---

# Outline: <Document Title>

> Document: <folder-name>
> Brief: .context/README.md
> Research: <available/not available>
> Constitution: <N principles extracted from brief>

## Objective Coverage Map

| Objective | Section(s) | Coverage |
|-----------|-----------|----------|
| ... | ... | Full/Partial |

## Executive Summary
- High-level overview of the document's purpose (1 paragraph)
- Key takeaways upfront — respect the audience's time
- Scope statement: what this document covers and doesn't cover
- *Serves: <objective(s)>*

## <Major Section 1>
- What this section establishes
- Key data or arguments to present
- Expected length: 2-3 paragraphs
- *Serves: <objective(s)>*
- *Principle note: <any specific principle that applies>*

### <Subsection 1a>
- Specific focus area
- Evidence or examples to include

### <Subsection 1b>
- Related but distinct point

## <Major Section 2>
...

## Conclusion / Next Steps / Recommendations
- How to close based on document type and objectives
- Call to action if appropriate for the audience

## Validation Notes
- Constitution warnings (if any principles couldn't be structurally enforced)
- Research gaps (if research had thin/missing coverage areas)
- Assumptions made in structuring

## HITL Review

Every item has a *(recommended)* default. To accept all defaults, proceed without a response. To override, list only the items you want changed (e.g., `S1.B, Q3.C`).

### Steering Opportunities

> **S** = Steering — approve, veto, or redirect a structural decision this outline committed to.

S1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)* C) <Option>

### Outstanding Questions

> **Q** = Question — resolve an open ambiguity so drafting can proceed.

Q1. **<Short label>** <One-sentence context.>
    A) <Option> *(recommended)* B) <Option> C) <Option> D) <Option>

### Scope Check

> **K** = Scope Check — agree to simplify the document structure or confirm the current approach.

K1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)*

---
*No response = all *(recommended)* defaults applied. Override format: `S1.B, Q3.C` (only the items you want to change). Free-form feedback also accepted. Resolve before running `/ai-doc-draft`.*
```

### 6d: Formulate HITL Review

Before writing the outline, formulate three categories of feedback items for the HITL Review block:

**Steering Opportunities (S)** — Structural decisions you committed to that the user should confirm:
- Section organization approach (e.g., "I organized by chronology rather than by importance")
- Depth allocation choices (e.g., "I gave the Risk section the most depth based on research strength")
- Content placement decisions (e.g., "I placed key metrics in the Executive Summary rather than a dedicated section")
- Section consolidation (e.g., "I combined Market Analysis and Competitive Landscape into one section")
- Frame as approve/veto/redirect. Each item: short label + one-sentence context + 2-4 choices.

**Outstanding Questions (Q)** — Decisions the user must make before drafting:
- Structural ambiguities (e.g., "Should the appendix include raw data tables?")
- Coverage depth questions (e.g., "How detailed should the methodology section be?")
- Audience-driven choices (e.g., "Should we assume the reader has seen the Q4 report?")
- Frame as A/B/C/D choices. Include a recommendation where research or brief supports one, marked *(recommended)*.

**Scope Check (K)** — Opportunities to simplify the document structure:
- "The outline has N major sections — should we consolidate?"
- "Should we cut [section] — it overlaps with [other section]?"
- "Is the subsection detail level appropriate, or would a flatter structure serve the audience better?"
- Frame as scope-check choices: simplify or keep the current structure.

**Item guidelines:**
- Target 2-5 items per subsection. Include a subsection only when genuine items exist — no forced filler.
- Minimum 2 items total across all subsections.
- Each item: 2-4 choices (A/B minimum, A/B/C/D maximum).
- Exactly one choice per item MUST be marked *(recommended)*. This is the default applied when the user does not override the item.
- Fixed order: Steering → Questions → Scope Check.

## Step 7: Validation Checklist

**ultrathink** — This is the last gate before the outline is written. Walk through every checklist item deliberately — interactions between structure quality, constitution compliance, and research integration are where outlines silently fail.

Before writing the outline to disk, run this checklist internally. Every item must pass.

**Structure Quality:**
- [ ] Every brief objective maps to at least one section (check coverage map)
- [ ] Section order is logical for the stated audience
- [ ] No section exists without a clear purpose tied to an objective or the document scope
- [ ] Heading hierarchy is consistent (no H3 without H2 parent)

**Constitution Compliance:**
- [ ] Every principle from the brief is addressable by the outline structure
- [ ] Any unaddressable principles are documented in Validation Notes
- [ ] Section guidance notes reference applicable principles

**Research Integration (if research.md exists):**
- [ ] Key findings from research are assigned to specific sections
- [ ] Research gaps are acknowledged (in Validation Notes or section guidance)
- [ ] Coverage Assessment categories from research map to outline sections

**Completeness:**
- [ ] Document has an opening section (executive summary, introduction, or overview)
- [ ] Document has a closing section (conclusion, next steps, or recommendations)
- [ ] No placeholder sections with empty guidance
- [ ] README.md scope boundaries are respected (outline doesn't cover out-of-scope topics)

**HITL Review:**
- [ ] HITL Review block is present with at least 2 items total across subsections
- [ ] Each item has 2-4 choices with short labels and one-sentence context
- [ ] Subsections only appear when they have genuine items (no empty subsections)
- [ ] Exactly one *(recommended)* marker per item

**If any item fails**: fix the outline before writing. Do not proceed with a failing checklist. If you cannot fix it (e.g., research gaps you can't fill), document the issue in Validation Notes.

## Step 8: Write the Outline

Write to `<doc-folder>/outline.md`.

If an `outline.md` already exists, overwrite it. The outline is regenerated, not appended. Tell the user you're replacing the existing outline.

## Step 9: Update Status and Confirm

Update `<doc-folder>/README.md` Status: check `[x] Outline`.

Tell the user:
- "Outline written to `<doc-folder>/outline.md`"
- Report the objective coverage map (brief summary — how many objectives covered)
- Report any constitution warnings or research gaps from Validation Notes
- Surface HITL Review items: list steering opportunities, outstanding questions, and scope check items (briefly — 1 line each)
- "Address the HITL Review items before running `/ai-doc-draft`"
- "Next: address HITL items, then `/ai-doc-draft <name>` to write the full document"
- "Edit the outline manually if you want to adjust the structure before drafting"

## Manifest Update

After updating status, update the docs manifest at `<docs_root>/README.md`:

1. Read `<docs_root>/README.md` (create from template if missing — see `references/manifest-update.md`)
2. Read this document's README.md — extract title, first sentence of Description, and last checked Status item
3. Find or append the row for this folder in the table (maintain alphabetical order)
4. Determine state emoji: 🆕 (README only) → 🔬 (Research) → 📝 (Outline) → ✏️ (Draft) → ✅ (Complete)
5. Update the row: `| [<folder>](<folder>/) | <emoji> <State> | <description> |`
6. Update the "Last updated" date in the blockquote
7. Write back with the Edit tool (preserve all other rows unchanged)
