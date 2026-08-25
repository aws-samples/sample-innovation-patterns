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

**Read the placement convention unconditionally.** Separately from resolving
`docs_path`, read `dirname(docs_path)/CLAUDE.md` **by path** — and the project
root's `CLAUDE.md` when that is a different file. This is rank 3 of the audience
resolution ladder (reference §12.3), and it is **not** conditional on `docs_path`
being absent: a project can carry `docs_path` in its context file and record where
a new page goes only in prose, so a read that fires only on a missing `docs_path`
never consults the top-ranked signal.
`.claude/skills/ai-skills-reference/framework-detection.md` ranks this signal
first for that reason. Do not rely on either file being in ambient context.

Also read the project's Voice, Key Terms, Principles, and Constraints from
`.context/README.md` — CREATE applies them to every page it writes. Read its
`## Audiences` section too, if it has one (reference §12.2). **Absence is the
normal case and is not a warning** — a project that declares no audiences has one,
and the axis selects nothing there.

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

### Step C0: Check which root the request belongs to

**Run this before C1.** A request that should never become a published page must
not be classified either — classifying it assigns a mode, and a mode assignment is
what sends it into the tree.

Reference §13 lists four documentation roots. This skill writes to exactly one of
them, the published docs tree. If the request names an artifact belonging to one
of the other three, **write no page** and report which skill owns it:

| The request names | Owner | Root |
|---|---|---|
| how a feature, subsystem, or module was actually built | `/ai-as-built` | the working root |
| an architectural decision, or a record of one | `/ai-adr` | the decision log |
| agent context for a source directory — a `CLAUDE.md`, or a directory's own `README.md` | `/ai-context` | agent context, by proximity |
| research, a plan, a design, an outline, or a draft | the working-root pipeline — `/ai-research`, `/ai-architect`, `/ai-plan`, `/ai-outline`, `/ai-draft` | the working root |

"Document how we built the release pipeline" is the case this step exists for. It
reads as a documentation request, resolves to no existing path, and therefore
reaches CREATE — where Mode Detection has already branched on path resolution
alone and nothing has yet asked which root it belongs to. Name `/ai-as-built` and
stop.

**One test, so this step does not swallow legitimate work.** A request for a page
*about* one of these things is still a page request: "explain why we keep a
decision log" is an explanation page, not a decision record. The discriminator is
whether the request asks for **the artifact itself** or for **a page addressed to
a reader who came to the site.** When it reads as both, ask with
`AskUserQuestion`, offering the two readings — the same posture Mode Detection
takes on an ambiguous argument.

### Step C1: Classify the request

Run **Shared: Classify** on the request text.

### Step C2: Gate

Run **Shared: The Conflation Gate**. A dual-intent request — e.g. "explain how
caching works and show me how to configure it" (cognition/acquisition +
action/application) — stops here and proposes two cross-linked pages. Write
nothing until the user confirms.

### Step C2b: Resolve the audience

**After the gate and before placement.** It cannot live in Mode Detection, which
resolves `$ARGUMENTS` against `docs_path` first and would then be reading the same
argument twice for two different purposes.

1. Work down the **five-rank ladder** in reference §12.3, stopping at the first
   rank that decides: the request's own words (matched by *position* — `for the
   <label>`, `<label>-facing`, `in <label> docs`, a leading `<label> docs:`), the
   `## Audiences` declaration, the placement convention read in Context Loading,
   the root detector, then the object test.
2. Run the **audience-root detector** (reference §12.4) on `docs_path`, so rank 4
   has an answer whether or not the project declared anything.
3. **Ask with `AskUserQuestion` on zero matches and on two.** Never guess, and
   never resolve a near-miss to the nearest label — reference §12.3 forbids fuzzy
   matching because a wrongly resolved audience produces no error anywhere.

**When no audience is known anywhere and the request named none, resolve to
`none` and print nothing about the axis.** Not a warning, not a suggestion, not a
mention. This is the ordinary single-audience project, and telling it about a
distinction that selects nothing is the noise this axis was designed to avoid.

### Step C3: Place the page

Place at **one of three paths**, according to what C2b resolved:

| C2b resolved | Page goes to |
|---|---|
| an audience whose root sits above the modes | `<audience-root>/<mode>/<slug>.md` |
| an audience that partitions from below | `docs_path/<mode>/<audience>/<slug>.md` |
| `none`, or an audience with no directory | `docs_path/<mode>/<slug>.md` |

**Create only the one directory the classified page needs.** Never scaffold the
other three modes — the anti-scaffold rule (reference §6) names empty mode
directories as the practice Diátaxis exists to prevent; a mode directory exists
because a page needed it.

**CREATE never creates an audience root.** An above-the-modes root needs a sidebar
entry and a navigation item that no skill in this collection writes (reference
§12.5), so creating one here would produce a page no reader can reach. When the
resolved audience has no directory, place at the mode root and report that.

**When the request named an audience and the project has none**, place at the mode
root and print **one line** saying so and naming how to declare one — a
`## Audiences` section in `.context/README.md` (reference §12.2). Not silence, and
not a question: the builder raised the audience, so answering is not unsolicited
noise, and staying silent would look like the phrase had been honoured.

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

### Step C5: Self-audit, report the resolution, and link

Confirm: one mode only; title rule satisfied; no `{` remains; the page uses the
matching template's sections. Then link the new page from its section index so
it is not an orphan.

**Report the resolved audience and the rank that resolved it — one line, every
run.** For example: `audience: developer, resolved from the request`. When C2b
resolved to `none` because the project declares no audiences and the request named
none, this line is **omitted entirely** rather than printed as "audience: none".

Treat the line as a hard requirement, not a nicety. A page filed under the wrong
reader renders correctly, links correctly, and passes `npm run build` — so nothing
downstream can fail on it, and this report is **the only check the axis has.** An
implementation that drops it to save a line has removed the feature's entire
verification. When the resolution is wrong, the user re-runs with an explicit
`for the <label>` phrase; this step reports and never offers to move the page.

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

Then take two measurements of the tree's *shape*, separately from the table:

1. **Count each mode directory's contents-list items against seven.** An item is
   one entry per page or per subdirectory, **excluding the directory's own index**,
   counted **non-recursively** (reference §12.6). Use the fence-aware extraction
   reference §10 requires — a naive scan is unreliable here, because
   `grep -m1 '^title:'` reports `ai-util-export-pdf.md` as titled "Quarterly
   Review" from inside a fenced example. Record every mode whose count is
   **greater than** seven; seven itself does not qualify.
2. **Run the audience-root detector** (reference §12.4) on `docs_path`. Record what
   it returns, including when it returns zero.

Report the per-mode counts either way. On this repository they are 1 / 6 / 4 / 5
for tutorial / how-to / reference / explanation, and the detector returns zero — so
neither measurement produces an action, and saying so is the result.

### Step S3: Propose exactly one next action

Propose **one** next action on **one** page — the highest-severity conflation.
Cite the anti-batch rule: "every step in the right direction is worth publishing
immediately" (<https://diataxis.fr/how-to-use-diataxis/>). Do not propose a
batch of fixes; one page, one action, regardless of how many conflations the
table holds.

**A grouping proposal ranks strictly below every outstanding conflation.** Emit it
as the single next action only when **no** conflation remains anywhere in the
table. A page serving two modes is a Diátaxis defect; a nine-item index is a
readability signal, and the second never displaces the first. The one-action-only
rule is unchanged by this: a run with a conflation left proposes that conflation
and stays silent about the count.

When a grouping *is* the action, propose one of the two remedies reference §12.6
takes from its source — a landing-page prose grouping, or a nested directory
inside that one mode — **show which pages fall under each group, and make no edit
to any file until the user confirms.**

**An undeclared audience root is reported and asked about, never adopted.** When
the detector finds a root the project has not declared in `## Audiences`, say what
was found and ask whether it is an audience — the posture `adr-format.md:82` takes
for an unrecognised status, where both silent defaults are wrong. Adopting it
would infer a taxonomy the project never stated. **Never propose migrating an
existing flat tree into an audience shape:** that moves every page and breaks
every cross-mode index link, and it is a human's deliberate choice.

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
- **No audience root, ever.** CREATE places at a mode root and reports when the
  resolved audience has no directory. An above-the-modes root needs a sidebar entry
  and a navigation item this skill does not write (reference §12.5), so creating
  one would produce pages no reader can reach. `/ai-diataxis-scaffold` is the only
  skill that creates one, and it prints those registration lines.
- **No migration into an audience shape, and no grouping at seven.** SURVEY reports
  an undeclared audience root and asks; it never adopts one and never proposes
  moving an existing flat tree. The grouping trigger fires **above** seven items,
  so a seven-item index is left alone (reference §12.6).
- **No functional-quality judgement.** It enforces structure and single-mode
  purity. It does not and cannot verify that a tutorial teaches, a how-to's
  steps work, or reference is accurate or complete (reference §7).
