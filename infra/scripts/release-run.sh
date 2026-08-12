#!/usr/bin/env bash
# Cut an internal release: tag origin and create a GitLab Release.
# Usage: infra/scripts/release-run.sh [major]
#
#   (no argument)  ordinary release — minor or patch, derived from history
#   major          major release — derives with --bump major
#
# Environment:
#   ADVISORY_CHANGELOG=1  treat a CHANGELOG.md mismatch as a warning rather than
#                         a failure. Set ONLY by the automatic path — see below.
#   CONFIRM_VERSION       required to equal the derived tag when the argument is
#                         `major`. Run once to learn the value, re-run with it.
#
# This script is called by TWO jobs: release:auto (automatic, on a merge to the
# default branch) and release (manual break-glass, which passes `major` through
# from its BUMP variable). They must do the same thing, which is why the sequence
# lives here rather than inline in .gitlab-ci.yml twice. Two copies of an
# eight-step sequence, one of which pushes tags, is the kind of duplication that
# diverges silently and gets discovered by a bad release.
#
# It performs NO trigger detection. Deciding whether a release should happen is
# the caller's job: the automatic path requires a release marker, the manual
# paths deliberately do not (that is what makes them break-glass).
#
# ---------------------------------------------------------------------------
# THE ORDERING IS THE DESIGN. Do not reorder these steps.
# ---------------------------------------------------------------------------
#
# 1. Derive, and no-op when there is nothing to release.
# 1b. Gate a major bump on CONFIRM_VERSION.
# 2. Assert the tag is absent on origin — before anything local is created.
# 3. Run release-check.sh, which asserts tag hygiene, that the tag matches the
#    derived version, and that CHANGELOG.md matches. It runs BEFORE tagging
#    because "a gate that fires after tagging is not a gate" — the tag would
#    already be on origin by the time it complained.
# 4. Generate notes, tag, push, create the Release object.
#
# `--cleanup=verbatim -F` on the tag is load-bearing, not stylistic. The public
# side (.github/workflows/release.yml) reads the tag annotation and requires it
# to contain `^## \[` headings; the default cleanup mode strips comment-looking
# lines and reflows content. verbatim also preserves the two-space nested
# indentation cliff.toml produces (its `trim = false` is mandatory for the same
# reason). Change this and the public release notes silently lose structure.

set -euo pipefail

BUMP_MODE="${1:-}"

if [ -n "$BUMP_MODE" ] && [ "$BUMP_MODE" != "major" ]; then
  echo "error: unknown bump mode: $BUMP_MODE" >&2
  echo "hint: usage: release-run.sh [major]" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 1. Derive
# ---------------------------------------------------------------------------

if [ "$BUMP_MODE" = "major" ]; then
  TAG=$(git-cliff --bump major --bumped-version)
else
  TAG=$(git-cliff --bumped-version)
fi

LATEST=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")

if [ "$TAG" = "$LATEST" ]; then
  echo "Nothing to release — derived version equals the current tag ($LATEST)."
  echo "Only conventional commits (feat:, fix:, ...) derive a new version."
  exit 1
fi

# ---------------------------------------------------------------------------
# 1b. Major gate, BEFORE anything is created. A gate that fires after tagging is
#     not a gate.
#
#     This lives HERE rather than in the calling job's script block, which is
#     where it used to live (the retired `release:major` job). In a job block it
#     guarded one invocation route; here it guards every one of them, including
#     a direct run from a workstation. A direct, unreviewed major is the least
#     safe act this script performs, so the gate belongs where the act does.
# ---------------------------------------------------------------------------

if [ "$BUMP_MODE" = "major" ] && [ "${CONFIRM_VERSION:-}" != "$TAG" ]; then
  echo "error: a major release requires explicit confirmation" >&2
  echo "would cut: $TAG" >&2
  echo "hint: re-run with CONFIRM_VERSION=$TAG" >&2
  echo "hint: the REVIEWED route to a major is 'release:prepare' with BUMP=major," >&2
  echo "      which opens a merge request and creates no tag. Prefer it." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 2. Assert absence on origin. This is also the double-tag guard: because every
#    release path calls this script, it covers both orderings — automatic then
#    manual, or manual then automatic.
# ---------------------------------------------------------------------------

if git ls-remote --tags origin "refs/tags/$TAG" | grep -q "$TAG"; then
  echo "error: tag $TAG already exists on origin — nothing to release" >&2
  echo "hint: $TAG has already been released. If the GitLab Release object is" >&2
  echo "      missing but the tag exists, run gitlab-release.sh directly:" >&2
  echo "        bash infra/scripts/gitlab-release.sh $TAG <notes-file>" >&2
  exit 1
fi

echo "Releasing $TAG"

# ---------------------------------------------------------------------------
# 3. Gate, before creating anything
# ---------------------------------------------------------------------------

bash infra/scripts/release-check.sh "$TAG" "$BUMP_MODE"

# ---------------------------------------------------------------------------
# 4. Generate notes, tag, push, publish internally
# ---------------------------------------------------------------------------

# --tag stamps the heading as "## [X.Y.Z] - <date>". Without it the notes are
# headed "## [Unreleased]", which is wrong on a tag that names a version — and
# the publish path's heading assertion looks for "## [".
#
# The notes are generated HERE, from current history, rather than read from the
# committed CHANGELOG.md. That is what makes the published notes complete even
# when work landed on the default branch while the release was under review.
if [ "$BUMP_MODE" = "major" ]; then
  git-cliff --bump major --unreleased --tag "$TAG" --strip all > /tmp/release-notes.md
else
  git-cliff --unreleased --tag "$TAG" --strip all > /tmp/release-notes.md
fi

if ! grep -q '^## \[' /tmp/release-notes.md; then
  echo "error: generated notes for $TAG contain no version heading" >&2
  echo "hint: .github/workflows/release.yml requires a '## [' heading in the tag" >&2
  echo "      annotation. Refusing to create a tag that would break the public" >&2
  echo "      release path. Nothing was created." >&2
  exit 1
fi

git tag -a "$TAG" --cleanup=verbatim -F /tmp/release-notes.md
git push origin "$TAG"

bash infra/scripts/gitlab-release.sh "$TAG" /tmp/release-notes.md

echo ""
echo "Released $TAG internally. Nothing was published to GitHub."
echo "To publish this tag publicly, run 'publish:github:plan' first, then"
echo "'publish:github' with the CONFIRM_TAG value it prints."
