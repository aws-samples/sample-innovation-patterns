# Mode Index Seed Shapes

The pages the scaffold skill writes: **four mode index pages**, one per Diátaxis
mode, and — only when the audience question returned audiences — **one landing page
per audience root**. Each is a complete page, not a fragment: a reader who opens a
freshly scaffolded tree finds prose that tells them what the mode is for and one
example of a page in it.

The four mode seeds are **generic by design**. Each describes its mode in reader
terms and carries a fenced example with no project specifics, because the scaffold
runs before any page exists to be specific about. Project-specific pages come from
`ai-diataxis` CREATE afterwards.

**The audience landing seed is the one exception, and it is a shape rather than a
copyable block.** Its content is *this* project's audience label and the object that
audience's readers act on, both of which come from the interview answer, so there is
nothing generic to copy. It uses `<angle-bracket>` slots and every one of them is
filled before the page is written — the no-`{` rule below covers braces, and an
emitted page carries no unfilled angle brackets either.

This file is shared byte-identically by both runtimes, so it names skills without
a leading slash and cites no path that only one runtime has.

## Rules that apply to all four

- **Frontmatter is exactly three keys:** `title`, `sidebar_label`,
  `sidebar_position: 1`. Position 1 puts the index at the top of its directory's
  sidebar; the pages added later take 2 and up.
- **Emit `.md`, never `.mdx`.** Under Docusaurus's `format: 'detect'` an `.mdx`
  file goes through the MDX compiler, where `{anything}` is a JSX expression and
  a stray brace fails the build.
- **No `{` character anywhere in an emitted page.** The worked examples are
  illustrative markdown, not template slots — write them filled in. This is
  checkable and it is checked (skill step 8).
- **Every relative link must resolve.** Each seed links to its sibling modes with
  a directory link (`../how-to/`), which resolves to that directory's own
  `index.md`. A seed therefore only links to modes that exist or are being
  created in the same run — never to a mode the scaffold skipped.
- **The worked example goes in a fence.** Fence-aware heading extraction ignores
  headings inside a fenced code block, so an example `# How to …` heading inside a
  fence does not make the index page look like a how-to.

## Naming rules the examples must honour

Two modes carry a title rule; tutorial and reference carry none — do not invent
one for them. Sources: <https://diataxis.fr/how-to-guides/> and
<https://diataxis.fr/explanation/>.

- **How-to** — the title must begin "How to", so it says exactly what the guide
  shows. "How to configure connection pooling", not "Configuring connection
  pooling" (which might be about whether you should) and not "Connection pooling"
  (which might be an explanation).
- **Explanation** — the title must read naturally after an implicit "About":
  "About connection pooling", "About the permission model."

## Seed: tutorial/index.md

````markdown
---
title: "Tutorial"
sidebar_label: "Tutorial"
sidebar_position: 1
---

# Tutorial

A guided lesson for a reader who has not used this project before. A tutorial's
job is to give them a first success, so it makes every choice on their behalf and
follows one path from start to finish — no options, no branches, nothing to
decide. What the reader learns is the shape of the thing; the exercise itself can
be small.

A tutorial is a lesson, so it says what the reader will build and takes them
through it:

```markdown
# Build your first report

By the end of this tutorial you will have a working report and will have used
the query builder, the formatter, and the export step.
```

Nothing here explains *why* the system works as it does — that belongs in
[explanation](../explanation/) — and nothing here assumes a goal the reader
brought with them, which is what a [how-to guide](../how-to/) is for.
````

## Seed: how-to/index.md

````markdown
---
title: "How-to Guides"
sidebar_label: "How-to"
sidebar_position: 1
---

# How-to Guides

Task-oriented directions for a reader who already knows what they want to
accomplish. Each guide assumes a goal and shows the shortest reliable route to
it. Nothing here teaches the system from scratch — that is the tutorial.

A how-to title begins "How to", so it says exactly what the guide shows:

```markdown
# How to configure connection pooling
```

For a reader who has never used this project, start with the
[tutorial](../tutorial/). For the reasoning behind a design, see
[explanation](../explanation/).
````

## Seed: reference/index.md

````markdown
---
title: "Reference"
sidebar_label: "Reference"
sidebar_position: 1
---

# Reference

Descriptions of how this project is built, for looking things up mid-task.
Reference mirrors the product rather than any workflow, so these pages are
organized the way the thing itself is organized — not in the order a reader
would work through them. Come here for a specific fact and leave with it.

Reference is austere and states what is, without instructing:

```markdown
## `--timeout`

Seconds to wait before abandoning a request. Integer, default 30. A value of 0
disables the timeout.
```

Reference can describe how something works. What it does not do is walk a reader
through a task — that is a [how-to guide](../how-to/) — or argue for a design,
which is [explanation](../explanation/).
````

## Seed: explanation/index.md

````markdown
---
title: "Explanation"
sidebar_label: "Explanation"
sidebar_position: 1
---

# Explanation

The thinking behind this project — why it is built this way, and what the
alternatives were. These pages are for understanding rather than doing: read them
to find out why a convention exists, or when a decision looks arbitrary and the
reasoning would help. Nothing here is needed to get a task done.

An explanation title reads naturally after an implicit "About", and the page
discusses rather than instructs:

```markdown
# About the permission model

Permissions are checked at the boundary rather than per record. That trades
some flexibility for a guarantee that no code path can skip the check.
```

For the steps to do something, see [how-to](../how-to/). For what a setting
does, see [reference](../reference/).
````

## Seed: the audience landing page

**Used only when the audience question returned audiences.** One per audience root,
written at `<audience-root>/index.md`. A shape to fill rather than a block to copy:
`<audience>` is the label the builder gave, and `<object>` is the thing that
audience's readers act on — *the released command-line tool*, *this repository's
source tree*. **The object is never a person.**

````markdown
---
title: "<Audience label, capitalised>"
sidebar_label: "<Audience label, capitalised>"
sidebar_position: 1
---

# <Audience label, capitalised> documentation

For readers working on <object>. Everything in this section is written for that
work; documentation for a different reader lives in its own section.

The four kinds of page here answer four different questions:

- [Tutorial](tutorial/) — teach me to use <object> for the first time
- [How-to guides](how-to/) — I already know what I want to do; show me the steps
- [Reference](reference/) — tell me exactly what this option does
- [Explanation](explanation/) — help me understand why it works this way

A page belongs to one of those four and to no other. Which one it belongs to
depends on what the reader needs at that moment, not on what the page is about.
````

**Filling it:**

- **Replace every `<slot>`.** A finished page contains no `<slot>` placeholder and
  no `{` character. Both are checked at skill step 8.
- **The mode links are relative to the root** — `tutorial/`, not `../tutorial/`.
  This page sits one level *above* the mode directories, where a mode index sits
  inside one. Getting this wrong sends every link to the other audience's tree, or
  out of the docs root entirely.
- **Name the object in the builder's own words from the interview, never a job
  title:** "the released command-line tool", not "end users". A label names the
  audience; the object names what they act on, and the two are not
  interchangeable.
- **Add a cross-link to the other roots only if there is more than one, and only to
  roots this run created.** A link to a tree that does not exist fails the build
  under `onBrokenLinks: 'throw'`.
- **Expect the modes to sort alphabetically in the sidebar, not in Diátaxis
  order.** All four mode index pages carry `sidebar_position: 1`, so inside one
  audience root they tie and an autogenerated sidebar falls back to alphabetical —
  explanation, how-to, reference, tutorial. Say so when handing over the
  registration lines. Renumbering them is not available here: the four mode seeds
  are shared with the no-audiences answer, which must stay byte-identical.

## The docs-tree `CLAUDE.md`

Written to the **parent** of `docs_path` when that parent is inside the docs site
rather than the project root, and only when no `CLAUDE.md` is already there.
Otherwise printed as a snippet. Never written to `docs_path` itself — under MkDocs
every `.md` below the docs directory becomes a page, so it would publish.

```markdown
# <docs directory name>/

Documentation content, organized by [Diátaxis](https://diataxis.fr) mode — one
directory per mode.

- `tutorial/` — learning-oriented: one guided path, no choices
- `how-to/` — task-oriented: the reader brings the goal
- `reference/` — information-oriented: mirrors the product
- `explanation/` — understanding-oriented: why, not how

A page serves exactly one mode. When a page starts serving two, split it rather
than adding a section — the mode a reader is in determines what they can absorb.
Put a new page in the directory matching what the reader needs, not what the
content is about.

A how-to title begins "How to". An explanation title reads naturally after an
implicit "About". Tutorial and reference titles carry no pattern.

`_templates/` holds the page templates and is not published. Directories whose
name begins with `_` are excluded from the build by convention.
```

### The audience variant

**Used only when the audience question returned audiences**, in place of the block
above — never in addition to it. On the default answer the block above is written
exactly as it stands, so that path acquires no prose about an axis the builder
declined.

Fill one `- <root>/` line per audience root from the interview answer.

```markdown
# <docs directory name>/

Documentation content, partitioned first by **audience** and then by
[Diátaxis](https://diataxis.fr) mode — one directory per audience, four per audience.

- <root>/ — for readers working on <object>
- <root>/ — for readers working on <object>

Inside each audience directory:

- `tutorial/` — learning-oriented: one guided path, no choices
- `how-to/` — task-oriented: the reader brings the goal
- `reference/` — information-oriented: mirrors the product
- `explanation/` — understanding-oriented: why, not how

A page's home is its **mode**. The audience directory says who the page is for; the
mode directory inside it says what kind of page it is, and it is the mode that
decides which of the four directories a page goes in. A page serves exactly one
mode. When a page starts serving two, split it rather than adding a section — the
mode a reader is in determines what they can absorb.

Put a new page in the audience whose readers act on the thing it describes, then in
the directory matching what those readers need — not what the content is about.

A mode index lists its pages flatly and gets grouped only once that list passes
seven items. Below that, grouping costs a reader more than the flat list does.

A how-to title begins "How to". An explanation title reads naturally after an
implicit "About". Tutorial and reference titles carry no pattern.

`_templates/` holds the page templates and is not published. Directories whose
name begins with `_` are excluded from the build by convention.
```

Replace every `<slot>` before writing. This file is agent context rather than a
published page, so the no-`{` rule does not reach it — but an unfilled slot here
misinforms every agent that reads it, which is worse than a broken build.

## The `AGENTS.md` snippet

Always printed, never written — no skill in this collection writes that file.

```markdown
## Documentation Structure

Documentation is organized by Diátaxis mode: `tutorial/`, `how-to/`,
`reference/`, `explanation/`. A page serves exactly one mode. Put a new page in
the directory matching what the reader needs, not what the content is about.
```
