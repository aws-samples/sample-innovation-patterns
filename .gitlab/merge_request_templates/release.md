## What this is

A **generated** release merge request, opened by `infra/scripts/release-prepare.sh`. It carries exactly one commit, which regenerates `CHANGELOG.md` for the derived version and changes nothing else.

The version was **derived** from Conventional Commit history — nobody typed it. There is no `VERSION` file.

## What to review

This is the only point at which a human reads the release notes before they are published. The questions worth asking:

- [ ] **Are the notes accurate?** Read the diff as the notes, because that is what they are. Does each entry describe what actually changed?
- [ ] **Is the derived version right?** A `feat:` gives a minor bump, a `fix:` a patch. If the version looks wrong, the commit *types* in the window are what to check.
- [ ] **Is anything missing?** Work committed with a non-conventional subject derives no bump and appears in no section — it is invisible here. If something shipped and is not listed, that is why.
- [ ] **Is anything present that should not be?** An internal-only change described in user-facing terms is worth rewording before it is published.

## Do not hand-edit CHANGELOG.md

The file is a build output. The next release regenerates it in full from `CHANGELOG_FLOOR`, so any edit made here is silently lost.

To correct an entry, change its **source** — the commit:

- **Wrong wording** — amend the commit body. `cliff.toml` renders the body as indented continuation text under each bullet, so prose belongs there.
- **Missing entry** — add an empty commit carrying the prose:

  ```bash
  git commit --allow-empty -m 'feat(scope): subject' -m 'body...'
  ```

Then re-run `release:prepare`. It is safe to run twice — it updates this branch rather than failing.

## What merging does

**Merging this tags the repository and creates the GitLab Release.** The `release:auto` job runs on the resulting pipeline for `main`, detects this release, and does it with no button press. This merge is the approval — there is no second confirmation after it.

A tag cannot be cleanly retracted, so read the notes before merging rather than after.

Merging publishes **nothing** to GitHub. Publication is a separate, confirmation-gated act (`publish:github:plan`, then `publish:github` with `CONFIRM_TAG`), and it can be done later or skipped entirely.

:::warning Do not edit the title
The merge request title is the marker `release:auto` looks for. Changing it means a squashed merge carries no marker, and the release silently does not fire.
:::

## If commits landed on main while this was open

The notes here were generated when this branch was cut, so a commit merged to `main` afterwards is not in them. The whole file is regenerated at every release, so a missing entry is recovered in the **next** release's section rather than lost.

To include it now, re-run `release:prepare` and review the updated diff.
