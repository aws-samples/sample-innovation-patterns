# Mode Index Seed Shapes

The four index pages the scaffold skill writes, one per Diátaxis mode. Each is a
complete page, not a fragment: a reader who opens a freshly scaffolded tree finds
prose that tells them what the mode is for and one example of a page in it.

Every seed below is **generic by design**. It describes its mode in reader terms
and carries a fenced example with no project specifics, because the scaffold runs
before any page exists to be specific about. Project-specific pages come from
`ai-diataxis` CREATE afterwards.

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

## The `AGENTS.md` snippet

Always printed, never written — no skill in this collection writes that file.

```markdown
## Documentation Structure

Documentation is organized by Diátaxis mode: `tutorial/`, `how-to/`,
`reference/`, `explanation/`. A page serves exactly one mode. Put a new page in
the directory matching what the reader needs, not what the content is about.
```
