---
name: ai-doc-research
description: "Research a topic for AI document generation, producing structured research output in a document folder. Use this skill when the user says 'aidoc research', 'research for my document', 'research this topic for the doc', 'gather information for the document', or wants topic research within the context of an aidoc project brief. Also trigger when the user says 'research <topic> for <document>'. Do NOT use for general codebase or code research (/research), writing or drafting documents (/ai-doc-draft), creating outlines (/ai-doc-outline), or any research unrelated to an aidoc document project."
model: opus
effort: max
---

# Agent Docs: Research

You research a topic for document production using an adversarial, gap-scanning approach. Before diving into research, you assess what's known vs. unknown, ask targeted questions to refine scope, then research comprehensively with a coverage summary.

## User Input

```text
$ARGUMENTS
```

Expected format: `[document-name] <topic>`

Examples:
- `/ai-doc-research q1-report market trends for Q1`
- `/ai-doc-research product-roadmap competitor analysis`
- `/ai-doc-research onboarding best practices`

## Step 1: Load Context

Read `.context/README.md` and parse `output_path.ai-doc` from frontmatter. Load the full brief context.
If not found: warn, suggest `/ai-init`, continue anyway.

## Step 2: Parse Arguments and Resolve Document Folder

The first token may be a document name. If it matches an existing folder in `<output_path.ai-doc>/`, treat it as the document name and the rest as the topic. Otherwise, treat the entire input as the topic and resolve the folder per common contract.
Read `<doc-folder>/README.md` for document-specific context (Description, Scope, Audience).

## Step 3: Coverage Scan (Inspired by speckit.clarify)

**ultrathink** — A shallow coverage scan leads to lopsided research — missing what the audience actually needs vs. what's easy to find. Think carefully about each of the 8 categories and where the real gaps are.

Before researching, perform a structured assessment of what is known vs. unknown about the topic. Use this taxonomy adapted for document research:

| Category | What to Assess |
|----------|---------------|
| **Subject Matter** | Core facts, data, and evidence needed for the document |
| **Audience Angle** | What the audience (from README + brief) specifically needs to know |
| **Data & Evidence** | Statistics, metrics, quantitative support available |
| **Expert & Authority** | Authoritative sources, expert opinions, institutional positions |
| **Contrasting Views** | Opposing perspectives, counterarguments, nuances |
| **Historical Context** | Background, precedent, how we got here |
| **Current State** | Latest developments, recent changes, current landscape |
| **Practical Examples** | Case studies, examples, analogies that illuminate the topic |

For each category, mark status: **Clear** (enough known), **Partial** (some gaps), **Missing** (significant unknowns).

This scan is internal — do not output it directly. Use it to prioritize research effort and to identify areas needing clarification.

## Step 4: Clarify Research Direction (Max 3 Questions)

If the coverage scan reveals critical ambiguities about what to research, ask up to 3 sequential clarifying questions before diving in.

Rules (from speckit.clarify patterns):
- Maximum 3 questions total
- Present ONE question at a time
- Each question has 2-4 options with a **Recommended** option and reasoning
- Only ask questions whose answers materially change the research direction
- If the topic is clear enough from the README + brief + user's description, skip questions entirely and proceed to Step 5

Example question:
```
**Recommended:** Option A - Focus on financial performance metrics, since the
audience is the Board of Directors and the document scope mentions Q1 results.

| Option | Description |
|--------|-------------|
| A      | Financial performance (revenue, margins, growth) |
| B      | Strategic initiatives (product launches, market entry) |
| C      | Risk and compliance (regulatory, competitive threats) |

Reply with the option letter, "yes" to accept the recommendation, or your own short answer.
```

## Step 4b: Parallel Source Research

When research spans multiple independent source types, spawn parallel agents to gather findings concurrently:

**Agent 1 (Web):** "Research <topic> using WebFetch. Target sources: <URLs from brief references and relevant authoritative sources>. Report: key findings, data points, quotes with citations, source credibility assessment."

**Agent 2 (Codebase):** "Search the codebase for implementations, patterns, and examples related to <topic>. Report: relevant code patterns, existing implementations, internal references, configuration details."

**Agent 3 (Docs):** "Read existing documentation in <doc paths> related to <topic>. Report: what's already documented, gaps, contradictions with current implementation, terminology usage."

Synthesize findings from all agents into unified research. Resolve contradictions between sources explicitly — note where web sources and codebase reality disagree.

**When to skip:** If the research topic is purely web-based (no codebase component) or purely code-based (no external sources), use only the relevant agent(s). Skip entirely if scope is narrow enough to handle in main context.

## Step 5: Research the Topic

**ultrathink** — Shallow synthesis misses contradictions between sources and overstates evidence that can't support the claims the document will make. Evaluate source credibility deliberately, identify contradictions, and assess evidence strength.

Conduct research using available tools (WebSearch, WebFetch, Grep, Glob, Read).

**Adversarial research posture** — don't just gather confirming evidence:
- Actively seek contradicting data or alternative perspectives
- Flag claims that lack strong sourcing
- Note where data is thin or outdated
- Identify assumptions that need validation
- Look for gaps the document's audience would notice

Frame all research through the combined context of:
- **Brief**: Project-level objectives, principles, constraints
- **README.md**: Document-specific scope, audience, purpose

## Step 5b: Formulate HITL Review

Before writing the research output, formulate three categories of feedback items for the HITL Review block:

**Steering Opportunities (S)** — Directions you committed to during research that the user should confirm:
- Research focus areas chosen (e.g., "I prioritized competitor data over market sizing")
- Source authority hierarchy assumed (e.g., "I treated industry reports as primary, blog posts as supplementary")
- Topic framing decisions (e.g., "I framed this through a risk lens rather than opportunity")
- Scope boundaries drawn (e.g., "I excluded historical context to focus on current state")
- Frame as approve/veto/redirect. Each item: short label + one-sentence context + 2-4 choices.

**Outstanding Questions (Q)** — Unresolved ambiguities needing user input before outlining:
- Audience knowledge assumptions that need confirmation
- Scope decisions that could go either way
- Content emphasis choices that depend on user priority
- Frame as A/B/C/D choices. Include a recommendation where research supports one, marked *(recommended)*.

**Scope Check (K)** — Opportunities to narrow the document's scope:
- "Is the research covering too many subtopics for one document?"
- "Should we cut [subtopic] — the evidence is thin and it's tangential?"
- "Is a simpler treatment sufficient for [area]?"
- Frame as scope-check choices: simplify or keep the current breadth.

**Item guidelines:**
- Target 2-5 items per subsection. Include a subsection only when genuine items exist — no forced filler.
- Minimum 2 items total across all subsections.
- Each item: 2-4 choices (A/B minimum, A/B/C/D maximum).
- Exactly one choice per item MUST be marked *(recommended)*. This is the default applied when the user does not override the item.
- Fixed order: Steering → Questions → Scope Check.

## Step 6: Write Research Output

Write to `<doc-folder>/research.md`:

```
---
title: "Research: <Topic>"
---

# Research: <Topic>

> Document: <folder name> | Brief: .context/README.md | Date: <date>

## Key Findings
- <Finding 1: concise summary with source reference [1]>
- <Finding 2 [2]>
- ... (5-10 key findings)

## Detailed Research

### <Subtopic 1>
<Findings, data, analysis with inline source references.>

### <Subtopic 2>
<More findings.>

## Sources
1. [Source title](URL or path) — what it provides
2. ...

## Coverage Assessment

| Category | Status | Notes |
|----------|--------|-------|
| Subject Matter | Strong/Partial/Thin | <what was found or is missing> |
| Data & Evidence | Strong/Partial/Thin | <...> |
| Contrasting Views | Strong/Partial/Thin | <...> |
| ... | ... | ... |

## Gaps & Caveats
- <Area where evidence is thin or contradictory>
- <Assumption that couldn't be verified>
- <Perspective that's missing and may matter to the audience>

## HITL Review

Every item has a *(recommended)* default. To accept all defaults, proceed without a response. To override, list only the items you want changed (e.g., `S1.B, Q3.C`).

### Steering Opportunities

> **S** = Steering — approve, veto, or redirect a direction this research committed to.

S1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)* C) <Option>

### Outstanding Questions

> **Q** = Question — resolve an open ambiguity so outlining can proceed.

Q1. **<Short label>** <One-sentence context.>
    A) <Option> *(recommended)* B) <Option> C) <Option> D) <Option>

### Scope Check

> **K** = Scope Check — agree to narrow the document's scope or confirm the current breadth.

K1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)*

---
*No response = all *(recommended)* defaults applied. Override format: `S1.B, Q3.C` (only the items you want to change). Free-form feedback also accepted. Resolve before running `/ai-doc-outline`.*
```

The Coverage Assessment and Gaps sections are the adversarial output — they tell the outliner and drafter where the document may be on shaky ground.

## Step 7: Update Status and Confirm

Update `<doc-folder>/README.md` Status: check `[x] Research`.

Tell the user:
- "Research written to `<doc-folder>/research.md`"
- Highlight any critical gaps from the Coverage Assessment
- Surface HITL Review items: list steering opportunities, outstanding questions, and scope check items (briefly — 1 line each)
- "Address the HITL Review items before running `/ai-doc-outline`"
- "Next: address HITL items, then `/ai-doc-outline <name>` to create a structured outline"

## Manifest Update

After updating status, update the docs manifest at `<docs_root>/README.md`:

1. Read `<docs_root>/README.md` (create from template if missing — see `references/manifest-update.md`)
2. Read this document's README.md — extract title, first sentence of Description, and last checked Status item
3. Find or append the row for this folder in the table (maintain alphabetical order)
4. Determine state emoji: 🆕 (README only) → 🔬 (Research) → 📝 (Outline) → ✏️ (Draft) → ✅ (Complete)
5. Update the row: `| [<folder>](<folder>/) | <emoji> <State> | <description> |`
6. Update the "Last updated" date in the blockquote
7. Write back with the Edit tool (preserve all other rows unchanged)
