---
name: ai-diataxis
description: "Create, assess, or survey documentation against the Diátaxis compass. Invoke ONLY via the /ai-diataxis slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."

effort: xhigh
---

# Agent: Classify Documentation Against Diátaxis

You place documentation on the Diátaxis compass and keep each page to a single
mode. You do three things depending on what you are given: **CREATE** a new page
from a request, **ASSESS** an existing page, or **SURVEY** a whole tree. You
never create empty mode directories, and you never emit a page that serves two
modes.

Standing up a whole mode tree in a project that has none is a different job and
belongs to `/ai-diataxis-scaffold`. That skill seeds every directory it creates,
so it does not make the empty structures the anti-scaffold rule names (reference
§6); the rule as it governs *this* skill is unchanged and unconditional.

The compass, the per-mode require/forbid criteria, the naming rules, the
adjacency warnings, and the connective rules all live in
`.claude/skills/ai-skills-reference/diataxis-classification.md`. Read it before
classifying anything. Everything normative in this skill traces to it.

## User Input

```text
$ARGUMENTS
```

## Mode Detection

Resolve `$ARGUMENTS` against `docs_path` **first**, before reading any verb.
Branch on what it resolves to:

- **Resolves to an existing page or directory** (a path under `docs_path`) → **ASSESS**.
- **Empty, or names `docs_path` itself** → **SURVEY**.
- **Describes content that does not exist** (a topic or request, not a path) → **CREATE**.
- **Ambiguous** — a description that also reads like a path, or a bare name that
  matches nothing on disk → ask with `AskUserQuestion`, offering the two
  readings as options. Never guess.

An **assess / review / audit / conformance** verb *reinforces* ASSESS but never
overrides path resolution: "review the caching page" resolves the path from "the
caching page" and the verb confirms it, but a review verb pointed at content
that does not exist is still CREATE. Path resolution wins.

Branching on `$ARGUMENTS` here does not violate the no-keyword-activation rule.
That rule governs which skill *fires* — this skill fires only from
`/ai-diataxis`. What it does *after* firing is ordinary dispatch.

---

## Shared: Context Loading

Run this once, before whichever mode you entered.

Read `.context/README.md` and resolve `docs_path` from its frontmatter:

- **Present and a string** → use it as the published docs root.
- **Present but not a string** → WARN: "docs_path in `.context/README.md` is not
  a string; using the detected docs root for this run." Do not block.
- **Absent** → detect the published root with the procedure in
  `.claude/skills/ai-skills-reference/framework-detection.md` (match a
  static-site config to its docs location). Confirm the detected path with the
  user via `AskUserQuestion`, with the detected path marked **(recommended)**.
  On confirmation, write `docs_path` into `.context/README.md` frontmatter with
  the Edit tool, and report that the interview will not repeat. Do not block if
  the user declines — proceed with the detected value for this run only.

Also read the project's Voice, Key Terms, Principles, and Constraints from
`.context/README.md` — CREATE applies them to every page it writes.

### The walk exclusion rule

Two things are excluded from every traversal in this skill:

1. **`output_path`** — the working root. In this repo `docs_path` is `docs/docs`
   and `output_path` is `docs/docs/working`, so the working root is *inside* the
   published tree. Any walk that fails to exclude it classifies research artifacts
   as publishable pages.
2. **Any underscore-prefixed directory** (`_templates/`, `_partials/`, `_drafts/`)
   at any depth under `docs_path`. This is the convention most static-site
   generators already use for content that is not published — Docusaurus's default
   `exclude` skips `**/_*/**`, and Jekyll and Hugo treat the prefix similarly.

Both are exclusions for the same reason: the files are **not published pages**, so
classifying them is a category error regardless of what they contain. An
underscore directory is not *connective* — connective means the page's job is
routing, and a template file routes nothing (reference §9). It is unpublished,
which is exactly what the `output_path` exclusion already models. A directory of
unfilled templates is the concrete case: `reference.md` carries `{placeholders}`
in H2 heading text, so a walk that includes it extracts those as headings and
classifies them.

**ASSESS (A1) and SURVEY (S1) both use this one rule; neither restates it.**
Capture the `output_path` value here and exclude both it and every
underscore-prefixed directory from any directory walk below.

---

## Shared: Classify (used by CREATE, ASSESS, SURVEY)

**ultrathink** — Classification is the whole job; a wrong mode assignment
propagates into a wrong template, a wrong title, and a wrong home. The compass
warns that "sometimes intuition provides an immediate answer that is also
wrong," so do not stop at the first read.

To classify one input (a request, or a page's real content):

1. Ask the compass's two questions — *action or cognition? acquisition or
   application?* — and read the mode off the four-row table in the
   classification reference (§1).
2. For a page, extract its headings **fence-aware** (reference §10): ignore any
   `##`/`###` inside a fenced code block. Classify the page's own content, not
   the scaffolding it documents.
3. Confirm the candidate mode against that mode's **require** and **forbid**
   lists (reference §2). If the content matches another mode's require list, or
   trips this mode's forbid list, it is either mis-classified or conflated —
   carry every mode you find evidence for into the gate below.
4. Do not classify by difficulty (reference §5). Do not enforce a mode's forbid
   list past its bounded permissions — reference may describe how something
   works; how-to sequences may fork (reference §2).
5. Skip **connective** pages (reference §9) — a directory index by the mechanical
   pattern rule, or a page on the closed enumerated list. They are exempt from
   classification and from the gate.

Record, for each mode you assign, the specific evidence (the heading, the
sentence, the title shape) that assigned it. Every downstream report cites it.

## Shared: The Conflation Gate (used by CREATE and ASSESS)

**ultrathink** — A page serving two modes is the failure this skill exists to
prevent. This is the one gate; CREATE (C2) and ASSESS (A2) both enter it. There
is no second gate.

Count the distinct Diátaxis modes the classify step found in the input.

- **One mode** → proceed.
- **Two or more** → **STOP.** Report each mode with the evidence that assigned
  it. Propose one page per mode, cross-linked. Make **no edit and no file** until
  the user confirms which split to take.

Never split without confirmation, and never auto-rewrite a published page on
classification confidence alone — that is exactly the "immediate answer that is
also wrong" the compass warns about. The gate always stops and asks.

---

## CREATE Mode

The request describes content that does not exist yet. Produce exactly one page,
in exactly one mode directory.

### Step C1: Classify the request

Run **Shared: Classify** on the request text.

### Step C2: Gate

Run **Shared: The Conflation Gate**. A dual-intent request — e.g. "explain how
caching works and show me how to configure it" (cognition/acquisition +
action/application) — stops here and proposes two cross-linked pages. Write
nothing until the user confirms.

### Step C3: Place the page

For the single confirmed mode, ensure its directory exists under `docs_path`
(`tutorial/`, `how-to/`, `reference/`, or `explanation/`). **Create only that
one directory if it is missing. Never scaffold the other three** — the
anti-scaffold rule (reference §6) names empty mode directories as the practice
Diátaxis exists to prevent; a mode directory exists because a page needed it.

### Step C4: Instantiate the template

Copy the matching template from `references/templates/` (reference §11:
tutorial → `tutorial.md`, how-to → `how-to.md`, reference → `reference.md`,
explanation → `concept.md`, a troubleshooting how-to → `troubleshooting.md`).
Then:

- Apply the naming rule (reference §3): a how-to title begins "How to"; an
  explanation title passes the implicit-"About" test. Tutorial and reference
  have no title rule.
- Fill the `{slots}` with real content. **Strip every `{placeholder}`** — a
  finished page contains no `{`.
- Apply the project's Voice, Key Terms, and Principles from context loading.
- Write the page at `docs_path/<mode>/<slug>.md`.

### Step C5: Self-audit and link

Confirm: one mode only; title rule satisfied; no `{` remains; the page uses the
matching template's sections. Then link the new page from its section index so
it is not an orphan.

---

## ASSESS Mode

The argument resolved to an existing page. Classify it; report; edit nothing
without confirmation.

### Step A1: Read and classify

Read the page at the resolved path (per the shared walk exclusion rule). Run
**Shared: Classify** on its real, fence-aware content.

### Step A2: Gate

Run **Shared: The Conflation Gate** — the *same* gate as C2, not a second one. A
page carrying a specification, a workflow, and rationale trips it as three modes.

### Step A3: Report

Report the detected mode(s) with evidence. For a single-mode page, state the
mode and whether its title and template sections conform. For a conflated page,
report each mode with its evidence and propose cross-linked pages — one per
mode. **Make no edit until the user confirms.** State plainly what the skill
checked (structure, mode, title, placeholders) and what it did not (whether the
content is accurate or teaches — reference §7).

---

## SURVEY Mode

No argument, or the argument named `docs_path`. Walk the whole published tree.

### Step S1: Walk

Walk `docs_path` under the **shared walk exclusion rule** — excluding
`output_path` and every underscore-prefixed directory. Collect every `.md` page
that is not connective (reference §9: a directory index by pattern, or an entry on
the closed enumerated list).

### Step S2: Classify and rank

Run **Shared: Classify** on each collected page. Build a table ranked by
**conflation severity** — pages serving the most modes first. Within the table:

- **Deprioritise `reference/skills/` pages.** They are correct
  *product-mirroring* reference: Diátaxis holds that reference should mirror the
  product's structure (reference §7), and these pages already mirror the
  installer's family layout. Deprioritised is not excluded — they still appear,
  ranked low.
- **Exclude connective pages outright** — they never enter the table.

### Step S3: Propose exactly one next action

Propose **one** next action on **one** page — the highest-severity conflation.
Cite the anti-batch rule: "every step in the right direction is worth publishing
immediately" (<https://diataxis.fr/how-to-use-diataxis/>). Do not propose a
batch of fixes; one page, one action, regardless of how many conflations the
table holds.

---

## Report

Close every run by naming all three modes so SURVEY stays discoverable, the way
`ai-init` prints its re-invocation forms:

- "Assess a page: `/ai-diataxis <path>`"
- "Survey the whole tree: `/ai-diataxis`"
- "Create a page: `/ai-diataxis \"<what you need to document>\"`"

## What This Skill Does NOT Cover

- **No manifest update and no folder status ladder.** Unlike the pipeline
  skills, this skill maintains no working-folder manifest and no status
  checklist — matching `ai-as-built` and `ai-context`, which also touch
  published docs without either. The asymmetry is deliberate: this skill writes
  to the *published* tree, which has no working-folder manifest to update.
- **No empty mode directories, ever.** It creates a mode directory only when a
  classified page needs it. **No mode tree in a project that has none** — that is
  `/ai-diataxis-scaffold`'s job, and it seeds every directory it creates rather
  than leaving it empty.
- **No auto-splitting.** The gate always stops and asks; it never rewrites a
  page on its own confidence.
- **No functional-quality judgement.** It enforces structure and single-mode
  purity. It does not and cannot verify that a tutorial teaches, a how-to's
  steps work, or reference is accurate or complete (reference §7).
