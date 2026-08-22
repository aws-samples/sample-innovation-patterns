# Diátaxis Classification Reference

Shared classification procedure for `/ai-diataxis`. This is the compass, the
per-mode require/forbid criteria, the naming rules, the adjacency ("blur")
warnings, and the checks the skill can and cannot make. Every normative claim
carries the primary source it comes from, so a reader can confirm it rather
than trust the paraphrase.

Diátaxis (Daniele Procida, <https://diataxis.fr>) types documentation into four
modes. The Good Docs Project (<https://thegooddocsproject.dev>) supplies the
page templates. The two are independent projects; where this file maps one onto
the other (explanation → Good Docs "concept"), that is this project's synthesis,
labelled as such.

---

## 1. The compass

Source: <https://diataxis.fr/compass/>

To place any piece of documentation, ask **two questions**:

> "action or cognition? acquisition or application?"

Then read the answer off this table (quoted from the compass page):

| If the content… | …and serves the user's… | …then it must belong to… |
|---|---|---|
| informs action | acquisition of skill | a tutorial |
| informs action | application of skill | a how-to guide |
| informs cognition | application of skill | reference |
| informs cognition | acquisition of skill | explanation |

Two cautions from the same page, both load-bearing for an agent:

- **Use the terms flexibly.** The page says to "use the compass's terms
  flexibly" and to "don't get fixated on the exact names." The axis matters more
  than the label.
- **Do not trust a fast answer.** "Worse, sometimes intuition provides an
  immediate answer that is also wrong." A confident first read is not evidence;
  check it against the require/forbid lists below.

---

## 2. The four modes — require and forbid

Each mode below carries a **require** list (what the source page says the mode
IS) and a **forbid** list (what the same page says it must NOT do). These are
the checkable criteria. Quotations are from the cited page.

### Tutorial — learning-oriented

Source: <https://diataxis.fr/tutorials/>

**Require** (the page's own characterisation):

- "A tutorial is always **learning-oriented**"; it is "a _practical activity,
  in which the student learns by doing_."
- "A tutorial in other words is a lesson." The relationship is "a kind of
  contract between teacher and student, in which nearly all the responsibility
  falls upon the teacher."
- The exercise "must be": "_meaningful_", "_successful_" (the pupil can complete
  it), "_logical_" (the path makes sense), and "_usefully complete_."
- "A tutorial must inspire confidence" — "your tutorial works for every user,
  every time."

**Forbid** ("Anti-pedagogical temptations" — the page names four):
"abstraction, generalisation", "explanation", "choices", "information."
Specifically:

- Not a how-to: "Its purpose is not to help the user get something done, but to
  help them learn."
- No explanation inline: "_A tutorial is not the place for explanation._"
  Instead "provide a link or reference to that explanation."
- No options or alternatives: "Your guidance needs to remain focused on what's
  required to reach the conclusion."

### How-to guide — task-oriented

Source: <https://diataxis.fr/how-to-guides/>

**Require** — the page's "How-to characteristics" list, verbatim:

- "focused on tasks or problems"
- "assume the user knows what they want to achieve"
- "action and only action"
- "no digression, explanation, teaching"

It "serves the work of the already-competent user"; its form is "an executable
solution to a real-world problem or task," and its "fundamental structure … is
a sequence."

**Forbid:**

- No teaching or explaining (the fourth characteristic above). "It's not the
  responsibility of a recipe to teach you how to make something"; a good recipe
  "excludes both teaching and discussion." If concepts or reference are
  important, "link to them."

**Bounded permission — do not over-enforce:** how-to sequences are not required
to be a single rigid line. The page says: "The sequences of action in a how-to
guide sometimes need to fork and overlap, and they have multiple entry and
exit-points." A guide that branches is still a valid how-to.

### Reference — information-oriented

Source: <https://diataxis.fr/reference/>

**Require:**

- "Reference material is **information-oriented**." It gives "technical
  descriptions of the machinery and how to operate it."
- "It should be **austere**"; "neutrality, objectivity, factuality."
- "One hardly _reads_ reference material; one _consults_ it."
- "There should be no doubt or ambiguity in reference; it should be wholly
  authoritative."
- Structure mirrors the product: "the structure of the documentation should
  mirror the structure of the product," "structured according to the structure
  of the machinery itself." (This is why `reference/skills/` mirroring the
  installer's family layout is correct reference, not a defect — see §7.)

**Forbid:**

- No how-to, no explanation, no opinion: "explain, instruct, discuss, opine, and
  all these things run counter to the needs of technical reference." "Instead,
  link to how-to guides, explanation and introductory tutorials."

**Bounded permission — do not over-enforce:** reference is not barred from
describing mechanism. The page: "it can and often needs to include a description
of how something works or the correct way to use it." A description of how
something works does NOT by itself make a reference page a conflation. What it
must not do is *instruct* (steps to follow) or *explain the why* (discursive
rationale).

### Explanation — understanding-oriented

Source: <https://diataxis.fr/explanation/>

**Require:**

- "Explanation is a discursive treatment of a subject, that permits reflection."
  It is "understanding-oriented."
- Its job is to "explain why things are so - design decisions, historical
  reasons, technical constraints." It answers "Can you tell me about …?"
- **Work vs. study.** Explanation "is documentation that it makes sense to read
  while away from the product itself" — "the only kind of documentation that it
  might make sense to read in the bath." It is "characterised by its distance
  from the active concerns of the practitioner." Reference and how-to are
  consulted *while working*; explanation is read *while studying, away from the
  product*. That distance is the discriminator.

**Forbid:**

- No instruction, no bare description: "In explanation, you're not giving
  instruction or describing facts - you're opening up the topic for
  consideration."
- "Keep explanation closely bounded." Letting instruction or reference "creep
  in interferes with the explanation itself."

> Do **not** use the phrase "could you disagree with this sentence" as an
> explanation test. It appears nowhere on the Diátaxis site; the work-vs-study
> distinction above is the actual test.

---

## 3. Naming rules

Only two modes carry a title rule. Tutorial and reference carry **none** — do
not invent one for them.

**How-to — the good / bad / very-bad ladder.** Source:
<https://diataxis.fr/how-to-guides/>. "Choose titles that say exactly what a
how-to guide shows."

| Rung | Example | Why |
|---|---|---|
| good | "How to integrate application performance monitoring" | says exactly what it shows |
| bad | "Integrating application performance monitoring" | "maybe the document is about how to decide whether you should, not about how to do it" |
| very bad | "Application performance monitoring" | "maybe it's about how - but maybe it's about whether, or even just an explanation of what it is" |

A how-to title must begin with "How to". (The page labels the middle rung
**bad**, not merely less good.)

**Explanation — the implicit "About" test.** Source:
<https://diataxis.fr/explanation/>. Explanation guides are "about a topic in the
sense that they are around it," and "you should be able to place an implicit (or
even explicit) about in front of each title." Examples: "About user
authentication", "About database connection policies." If a candidate title
reads naturally after the word "About", it is explanation-shaped.

---

## 4. Adjacency ("blur") warnings

Source: <https://diataxis.fr/map/>

Neighbouring modes share a quality and so bleed into each other. Watch these
four pairs; a page near a boundary is where conflation happens.

| Shared quality | Pair that blurs |
|---|---|
| "guide action" | tutorial ↔ how-to |
| "serve the application of skill" | how-to ↔ reference |
| "contain propositional knowledge" | reference ↔ explanation |
| "serve the acquisition of skill" | tutorial ↔ explanation |

"The different kinds of documentation bleed into each other," and the worst case
is "a complete or partial collapse of tutorials and how-to guides into each
other."

**Discriminator table** (same page) — use it to break a tie:

| Mode | Answers the question | Form | Orientation |
|---|---|---|---|
| Tutorial | "Can you teach me to…?" | "a lesson" | learning |
| How-to | "How do I…?" | "a series of steps" | goals |
| Reference | "What is…?" | "dry description" | information |
| Explanation | "Why…?" | "discursive explanation" | understanding |

---

## 5. Difficulty is independent of mode

Source: <https://diataxis.fr/tutorials-how-to/> — **not** the how-to page, which
argues a different point about trivial steps.

A common error is to split tutorial from how-to by how hard the material is.
Diátaxis rejects this: "a tutorial can present something complex or advanced.
And, a how-to guide can cover something that's basic or well-known." "How-to
guides can, do and often should cover basic procedures." The real line is
purpose: "The difference between the two lies in the need they serve: **the
user's study**, or **their work**." Do not classify by difficulty.

---

## 6. Rejected practices

Source: <https://diataxis.fr/how-to-use-diataxis/>

**Anti-scaffold rule (first and foremost).** Diátaxis names creating the four
**empty** mode directories up front as the practice to avoid. The page is
unusually blunt about it. Getting started "certainly does not mean that you
should create empty structures for tutorials/howto guides/reference/explanation"
— structures "with nothing in them." And then: "Don't do that. It's horrible."

So: a mode directory exists **because a page needed it**. Never create
`tutorial/`, `how-to/`, `reference/`, or `explanation/` empty and ahead of a
page. CREATE mode makes exactly the one directory the classified page requires
and no other.

**Scope of the prohibition.** The rule as published addresses projects that
*already have documentation*. Its context is the improvement cycle the same page
recommends, whose first step is "**Choose something** - any piece of the
documentation," with the instruction to "Just look at what you have right in
front of you at that moment: the file you're in, the last page you read." That
step presupposes documentation to choose from. The source is silent on a project
that has none — it neither permits nor forbids standing up a tree there, because
the case does not arise in the workflow it describes.

**The spirit is broader than the letter, and a scaffold deviates from it.** The
page's claim is not merely that empty directories are bad; it is that structure
should not be imposed at all: "**Diátaxis changes the structure of your
documentation from the inside**," and "Good structure develops from within" —
documentation builds "itself up from the inside-out, one cell at a time." Any
skill that stands up a mode tree ahead of the pages that would have created it
is working against that, whether or not the directories it makes are empty. Such
a skill must not claim source support for what it does. It deviates knowingly, on
an argument of its own, in a case the source does not reach.

**Provenance of this scoping.** The question was raised once before and was never
argued. HITL item S1 in the prior research —
`docs/docs/working/2026-07-30-docs-diataxis-framework/research.md:684` — offered
scaffold-first as option (B) and greenfield-only scaffolding as option (C), and
resolved to the recommended default (A) by silence:
`plan-diataxis-skill.md:730` records that "All 18 research HITL items resolved to
their recommended defaults." This amendment therefore overrides an unexercised
default rather than reversing a considered ruling.

**Do not auto-split on intuition.** Because "sometimes intuition provides an
immediate answer that is also wrong" (§1), the skill never rewrites or splits a
page on its own classification confidence. It stops and asks (the conflation
gate).

---

## 7. What the skill can and cannot check

Source for the disclaimer: <https://diataxis.fr/quality/>

Diátaxis is explicit that it does not judge whether documentation is *good*:
"**Diátaxis cannot address functional quality in documentation.**" Functional
quality is "accuracy, completeness, consistency, usefulness, precision" —
"objectively-measurable standards." Diátaxis "works very effectively to
_expose_ lapses in functional quality," but its role there "can have only an
_analytical_ role." So state the skill's reach honestly:

**CAN check (structural):**

- Mode assignment against the compass and the require/forbid lists.
- Single mode per page (the conflation gate).
- Title patterns: how-to begins "How to"; explanation passes the "About" test.
- Template section presence (the page uses the matching vendored template).
- No unfilled `{placeholders}` remain on a finished page.
- No orphan: a new page is linked from its section index.

**CANNOT check (functional):**

- Whether a tutorial actually teaches, whether a how-to's steps work, whether
  reference is accurate or complete, whether an explanation is correct or
  illuminating. Never claim the skill verifies any of these.

**Product-mirroring reference is correct, not a defect.** Because reference
"should mirror the structure of the product" (§2), the `reference/skills/` pages
that mirror the installer's family layout are reference done right. SURVEY
deprioritises them rather than flagging them.

---

## 8. Thin-page check

Anchored on The Good Docs Project's **published caps only** — step count and
completion time. There is **no** published word-count rule; do not invent one or
attribute one to Good Docs. Word count is a weak secondary signal at most.

- **How-to.** Source: `how-to/guide_how-to.md` (TGDP, tag v1.6.0). "Focus only
  on one task in your how-to and restrict to a maximum of 8-10 steps per task."
  A how-to well over 10 steps is a candidate for splitting into sub-tasks; a
  how-to with one step is a candidate thin page. Count steps.
- **Tutorial.** Source: `tutorial/guide_tutorial.md` (TGDP, tag v1.6.0).
  "Ideally, your tutorial should take 15 to 60 minutes to complete." Estimate
  from step and section count, not word count.

Report thin-page findings as weak signals for a human, never as a hard failure.

---

## 9. The connective category — this project's extension

**This is not Diátaxis doctrine.** Diátaxis has four modes and no fifth. This
project adds "connective" as a local label for pages whose job is to route or
record rather than to teach, instruct, describe, or explain — index/router
pages, the migration note, and archived deprecated pages. They would be
mis-classified as conflations by the compass because they legitimately carry
fragments of several modes. **Connective pages are excluded from conflation
checks entirely.**

### The directory-index pattern rule

One class of connective page is recognised **by pattern rather than by list
membership**: a page that is the index of its own directory. Concretely, a page
is connective when its filename is `index.md` — or `README.md` where that file
serves as the directory's index — and it sits in a directory whose other contents
it introduces.

This rule is **mechanical and confers no discretion.** The test is the filename
and the directory-index role, and nothing else. It is **not** the page's content,
and it is **not** an agent's assessment of the page's purpose: a page that reads
like a router but is named `overview.md` is classified normally, and a page named
`index.md` is connective even if its prose looks like explanation. An agent that
finds itself reasoning about whether a page "is really doing routing" has left the
rule and is making the judgment call the closure below forbids.

The rule exists because the enumerated list below names *this* repository's index
pages by literal path. Without it, every other project's index pages are
classified normally, and because SURVEY ranks by conflation severity, a freshly
scaffolded tree's router pages sort to the top of the table — the skill would
propose a fix to a page the same toolchain had just written.

### The enumerated list

Beyond directory indexes, the list is **closed and enumerated**. An agent may
**not** add to it by judgment — a page not on this list, and not a directory index
under the rule above, is classified normally. The closure still binds for every
non-index page: the migration note and the nine deprecated skill pages below are
connective only because they are enumerated here, and nothing else earns that
label by resemblance to them.

Router / index pages (8 — all also satisfy the pattern rule above, so the
enumeration is redundant for them and kept only as a record):

1. `docs/docs/index.md`
2. `docs/docs/tutorial/index.md`
3. `docs/docs/how-to/index.md`
4. `docs/docs/reference/index.md`
5. `docs/docs/explanation/index.md`
6. `docs/docs/reference/skills/README.md`
7. `docs/docs/reference/skills/ai-util/index.md`
8. `docs/docs/reference/skills/deprecated/index.md`

Migration note (1):

9. `docs/docs/reference/skills/migration-v2.md`

Deprecated skill pages under `reference/skills/deprecated/` (9; the directory's
`index.md` is already item 8):

10. `ai-code-agent-context.md`
11. `ai-code-create.md`
12. `ai-code-implement.md`
13. `ai-code-plan.md`
14. `ai-code-research.md`
15. `ai-doc-create.md`
16. `ai-doc-draft.md`
17. `ai-doc-outline.md`
18. `ai-doc-research.md`

---

## 10. Fence-aware heading extraction

Classification reads a page's headings. A naive `grep '^## '` is wrong for this
repo, because SKILL.md files and many docs pages emit **example headings inside
fenced code blocks** — template scaffolds the page is *documenting*, not
headings the page *has*.

**Rule:** when scanning for a page's own headings, ignore any `##`/`###` line
that sits inside a fenced code block (between a ` ``` ` or `~~~` open and its
close). Only headings outside fences count.

**Worked example.** On `.claude/skills/ai-init/SKILL.md`:

- Naive `grep -c '^## '` returns **12**.
- A fence-aware scan returns exactly **4** real H2 headings — `## User Input`,
  `## Mode Detection`, `## Create Mode`, and `## Refine Mode`. The other 8 sit
  inside the template fences the skill emits (the `## Project`, `## Objectives`,
  … lines are inside the scaffold block the skill writes, not headings the skill
  file itself has).

If a scan of that file returns 12, the extraction is not fence-aware and every
classification built on it is unreliable.

---

## 11. Template mapping

Vendored templates live in `ai-diataxis/references/templates/` (Good Docs, tag
v1.6.0, MIT-0). One per mode:

| Diátaxis mode | Template file | Note |
|---|---|---|
| tutorial | `tutorial.md` | direct |
| how-to | `how-to.md` | direct; troubleshooting is also how-to |
| reference | `reference.md` | direct |
| explanation | `concept.md` | **synthesis** — Good Docs has no explanation template (that path 404s at v1.6.0 while `concept` returns 200), so explanation maps to `concept` |
| (how-to variant) | `troubleshooting.md` | a distinct page shape; Diátaxis classifies troubleshooting as how-to |

When instantiating a template: keep `{fill-in slots}` as braces until filled,
strip every `{placeholder}` before the page is considered finished, and apply
the project's Voice, Key Terms, and Principles from `.context/README.md`.
