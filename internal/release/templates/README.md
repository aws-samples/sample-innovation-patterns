# Portable Release Standard

A release practice you can adopt in any git repository. It needs `make`, `git`, and [`git-cliff`](https://git-cliff.org) — no CI system, no particular forge, and no framework.

## Adopt it

```bash
cp cliff.toml   /path/to/your/project/
cp release.mk   /path/to/your/project/
brew install git-cliff     # or see https://git-cliff.org
```

Then:

```bash
make -f release.mk release-preview   # what would be released; creates nothing
make -f release.mk release           # changelog + annotated tag (+ forge, if any)
```

Nothing in either file names a specific project, so there are no values to substitute.

## What each file does

| File | Role |
|------|------|
| `cliff.toml` | Maps Conventional Commit types to changelog sections, and controls how the next version is derived |
| `release.mk` | The targets: `release-preview`, `release-changelog`, `release-tag`, `release-forge`, `release` |

## The idea

**The version is derived, never stored.** A `VERSION` file conflates two different questions — "what is the next version?" (a release-time derivation from history) and "what is the current version?" (a build-time display) — and, being hand-maintained, drifts from the tags that actually define releases. `git-cliff --bumped-version` answers the first; `git describe` answers the second.

**Commit messages are the input.** A `fix:` commit derives a patch bump, `feat:` a minor. A commit matching no conventional type derives nothing and appears in no changelog section — so the format is not a style preference, it is the thing that determines whether work is recorded.

**The notes ride on the annotated tag.** That makes the tag self-describing: any clone can read the release notes for a version without a changelog file, a forge API, or network access.

## What you must decide for yourself

1. **Pre-1.0 behavior.** `cliff.toml` ships with `breaking_always_bump_major = false`, so a `feat!:` commit derives `0.x+1` rather than `1.0.0` — reaching a major becomes a deliberate act (`git-cliff --bump major`). This is **inert** once your major version reaches 1: after that, a breaking change derives the next major normally. Delete it if you want `feat!:` to mean `1.0.0` immediately.

2. **The `^Update:` skip parser.** Delete it in a new project. It exists as the pattern to copy when you inherit a repository whose history predates the convention: one skip parser neutralizes the changelog symptom without rewriting history.

3. **Whether to commit `CHANGELOG.md`.** The `release` target writes it and leaves it uncommitted for review. Because the notes also travel on the tag, a committed changelog is a convenience rather than a requirement — which means you can skip the CI commit-back machinery (protected-branch push rights, `[skip ci]` loop guards) entirely.

4. **Compare links.** Deliberately not generated. If your published tags are ever a subset of your internal tags, a compare link between two adjacent changelog versions is a 404 by construction. Tags and forge Release objects are the durable record. Add a `footer` to `cliff.toml` if you publish every tag and want them.

## Behavior when there is no forge

`release-forge` **skips rather than fails**:

- No `origin` remote → the tag is created locally and you are told to push it yourself later.
- Remote but no `gh`/`glab` CLI → the tag is pushed; no Release object is created, and you are told the annotation already carries the notes so a Release can be made later.
- `NO_PUSH=1` → nothing is pushed.

`make -f release.mk release` therefore succeeds in a repository with no remote at all. A release target that failed in that case would be unusable rather than merely limited.

## The one hazard worth knowing

`git tag -a -m "$NOTES"` **destroys every Markdown heading** in the notes. Git's default `--cleanup=strip` treats `#`-leading lines as comments, deletes them, **exits 0**, and warns nobody — so the tag looks fine and carries a flat, ungrouped, unversioned bullet list.

`release.mk` writes the annotation with `--cleanup=verbatim -F <file>` and then asserts the headings survived, deleting the tag if they did not. Keep both halves if you adapt it: the assertion is what makes the failure visible.

Reading the body from a file rather than a shell variable also avoids quoting problems with the backticks and asterisks that appear in real release notes.
