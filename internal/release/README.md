# Internal Release

Assets supporting IPA's release process. The process has **two independent stages**, and understanding the split is most of understanding the release path.

| Stage | Where | Jobs | Effect |
|-------|-------|------|--------|
| 1 — internal release | GitLab | `release:preview`, `release`, `release:major` | Derives a version, tags `origin`, creates a GitLab Release. **Publishes nothing publicly.** |
| 2 — public publish | GitLab → GitHub | `publish:github:plan`, `publish:github` | Publishes a **chosen** tag to the public mirror with cumulative notes. |

Stage 1 is documented in the [releasing runbook](../../docs/docs/developer-docs/internal/operations/runbooks/releasing.md). This file documents stage 2.

## What publishing actually withholds

**Publishing does not withhold code.** The publish path amends the tip and force-pushes `main`, so the code of an internal release you never published still reaches the public repository the next time you publish anything.

What publication withholds is **tags and Release objects**. That is what makes cumulative release notes a correctness requirement rather than a courtesy: a gap in the public tag sequence describes real, already-public code that no Release object documents. So the notes for a publish must cover everything since the last publish, not just the newest version.

## The floor

The **floor** is the newest version already published to GitHub. It is resolved by listing tags on the GitHub remote, filtering to strict semver, and taking the highest.

```bash
git ls-remote --tags github | awk '{print $2}' | sed 's|^refs/tags/||' \
  | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1
```

Three details are load-bearing:

- **GitHub is the only authority on what GitHub has.** A marker file tracking "last published" would be a second source of truth, and drift means either republishing notes or silently dropping a version's worth.
- **`sort -V`, not `sort`.** Plain `sort` ranks `v0.1.2` above `v0.1.10` — verified, and it will matter the first time a patch number reaches double digits.
- **The floor supplies a NAME, not a commit.** GitHub's tag objects point at *amended* commits (the filtered tree has different SHAs by construction), so the notes range must resolve both endpoints against `origin`'s tags of those names.

The notes window is `FLOOR..TAG`, **exclusive of the floor**, which is exactly "everything since the last publish."

## Usage

```bash
# Preview: prints TAG, FLOOR, the full notes body, the filtered-path report,
# and the CONFIRM_TAG value to supply. Publishes nothing.
internal/release/publish-github.sh --dry-run

# Publish a specific tag — including an older one.
TAG=v0.4.0 internal/release/publish-github.sh --dry-run
CONFIRM_TAG=v0.4.0 TAG=v0.4.0 internal/release/publish-github.sh
```

In CI, run `publish:github:plan` first and read the `CONFIRM_TAG` value out of its output. Publishing an older tag retags nothing internally — the internal tag already exists and is correct; only the public side is being brought forward.

## Hazards

Each of these fails **silently** if mishandled, which is why the script asserts rather than trusts.

### The tag annotation loses its headings

`git tag -a -m "$NOTES"` destroys every `##` and `###` heading. Git's default `--cleanup=strip` treats `#`-leading lines as comments, it **exits 0**, and it warns nobody — so a release published that way carries a flat, ungrouped, unversioned bullet list and nothing signals the loss.

The publish path builds the tag object with `git mktag`, which stores the body byte-for-byte, and then asserts the headings survived. `.github/workflows/release.yml` asserts again when reading it back.

### Force-moving tags in the operator's clone

`git tag -f` is what corrupted local `v0.1.7`: the old `github-push.sh` retagged in the invoking clone after amending, leaving the local tag pointing at a mirror-amended commit while `origin` held a different commit for the same name. That disagreement poisons both version derivation (`git describe` returns the previous tag) and any publish range.

**A worktree does not fix this.** Worktrees isolate the index, HEAD, and checkout — they share `refs/tags` with the main repository, so `git tag -f` inside one still moves the operator's tag. The publish path therefore writes **no local ref at all**: it builds the annotated tag object with `git mktag` and pushes it by SHA.

`release-check.sh` asserts local tags agree with `origin` on every release, so a recurrence is caught rather than discovered.

### `--force-with-lease` is not a divergence guard

The lease compares against `refs/remotes/github/main`, and a fresh clone establishes that ref at whatever the remote currently holds. So the lease passes precisely when a fresh clone is used — which is always, in CI. It protects against a stale local view, not against clobbering public work.

The real guard is an explicit content assertion. It is kept alongside the lease, not instead of it.

### The ancestry check must unshallow first

`.git/shallow` can contain the mirror tip, in which case `git merge-base --is-ancestor` answers from a one-commit graph and **fails closed** — reporting "not an ancestor" for commits that genuinely are ancestors. An assertion that always fails is worse than none, because operators learn to bypass it.

The publish path unshallows before reasoning about history.

### Behind is not divergent

The mirror's commits are amended versions of internal commits: different SHAs, identical content, by design. So a commit-identity comparison reports every mirror commit as divergent even when the mirror is perfectly reconciled.

The assertion compares **content**, and excludes deliberate removals (the internal-only path filter, plus files deleted by an internal commit). Being behind is a mirror's normal state and proceeds. Only content the mirror holds and the internal line lacks stops the publish — and the failure names it, because the mirror accepts pull requests and a force-push can destroy work that did not originate internally.

## Files

| File | Role |
|------|------|
| `publish-github.sh` | The single implementation: floor resolution, cumulative notes, verbatim tag object, filtered tree, divergence assertion, `--dry-run` |
| `../../infra/scripts/github-push.sh` | Deprecated wrapper delegating here, so exactly one implementation exists |
| `../../infra/scripts/release-check.sh` | Tag hygiene + derived-version assertions (stage 1) |
| `../../infra/scripts/gitlab-release.sh` | Creates the GitLab Release object for a tag (stage 1) |
| `../../.github/workflows/release.yml` | Reads the tag annotation and creates the GitHub Release |

## Known limitation: tag pushes do not trigger the customer pipeline

The generated customer CodePipeline triggers on branch references only — `referenceType: [branch]` in both `infra/cfn/codepipeline/codepipeline.yml` and `infra/tf/codepipeline/main.tf`. Tag pushes are inert.

This is documented rather than worked around: changing it would touch a deployed CloudFormation template, its Terraform twin, the stack skill, and CloudFormation/Terraform parity, to enable a trigger nothing currently asks for.
