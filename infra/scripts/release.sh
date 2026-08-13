#!/usr/bin/env bash
# Cut an internal release: tag origin and create a GitLab Release.
#
# Usage: infra/scripts/release.sh
#
#   Takes NO arguments. The version is DERIVED from tags and Conventional Commit
#   history — there is no VERSION file and no way to request a version. That is
#   deliberate: a requestable version is a version somebody gets wrong.
#
# Environment:
#   PREVIEW=1         print what would be released and exit 0. Creates nothing,
#                     and needs no network.
#   CONFIRM_VERSION   required, equal to the derived tag, when the release
#                     raises the MAJOR version.
#
# Runs identically in CI (the gitlab:release job) and from a workstation, which
# is what makes a release possible when CI is unavailable.
#
# Cutting an internal release publishes NOTHING publicly. Publication to the
# GitHub mirror is a separate, deliberate act — see internal/release/README.md.
#
# ---------------------------------------------------------------------------
# THE ORDERING IS THE DESIGN. Do not reorder these steps.
# ---------------------------------------------------------------------------
#
#   1. Derive.                Everything below is a statement about this value.
#   2. Preview, exit 0.       First, because everything below touches the network.
#   3. No-op, exit 0.         "Nothing to release" is an answer, not a failure —
#                             but only once origin confirms the tag was pushed.
#   4. Major guard.           Refuse before spending work on notes.
#   5. Tag hygiene.           A disagreeing tag means derivation read the wrong base.
#   6. Tag absence.           The double-tag guard.
#   7. Notes + heading assert.
#   8. Tag, push, Release object.
#
# Steps 4-7 all run BEFORE the tag exists, because a gate that fires after
# tagging is not a gate — the tag would already be on origin by the time it
# complained.

set -euo pipefail

if [ "$#" -gt 0 ]; then
  echo "error: release.sh takes no arguments (got: $*)" >&2
  echo "hint: the version is derived from commit history, not supplied. To" >&2
  echo "      preview, run: PREVIEW=1 bash infra/scripts/release.sh" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 1. Derive
# ---------------------------------------------------------------------------

TAG=$(git-cliff --bumped-version)
LATEST=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")

# ---------------------------------------------------------------------------
# 2. Preview
# ---------------------------------------------------------------------------
#
# One script, one early return, rather than a separate preview path — so the
# preview cannot report notes that differ from what a release publishes. The
# inline preview this replaces had exactly that drift: it omitted --tag, so it
# printed "## [Unreleased]" where a release prints "## [X.Y.Z] - <date>".
#
# FIRST, before every other check, because none of the others are network-free:
# even the no-op below asks origin whether the newest tag was pushed. A preview
# that requires the network is a preview that fails on a plane. The cost is that
# a preview does not detect a poisoned clone — acceptable, because it creates
# nothing and the release path still refuses.

if [ "${PREVIEW:-}" = "1" ]; then
  echo "current release: $LATEST"
  echo "would release:   $TAG"

  if [ "$TAG" = "$LATEST" ]; then
    echo ""
    echo "Nothing to release — no commits since $LATEST affect the version."
    echo "Only conventional commits (feat:, fix:, ...) derive a new version."
    exit 0
  fi

  echo ""
  echo "--- release notes for $TAG ---"
  git-cliff --unreleased --tag "$TAG" --strip all
  echo "--- end release notes ---"
  echo ""
  echo "Nothing was created. To cut this release, run the 'gitlab:release' job."
  exit 0
fi

# ---------------------------------------------------------------------------
# 3. The idempotent no-op
# ---------------------------------------------------------------------------
#
# Exits 0 DELIBERATELY. The release job is a button that can be clicked
# speculatively, and a red pipeline for "you clicked it and there was nothing to
# do" is a red pipeline everyone learns to ignore — at which point it also hides
# the one time it means something.
#
# But "derived equals newest" has TWO causes, and only one of them is nothing to
# do. If a previous run created the tag locally and then failed to push it,
# `git describe` reports it, derivation reports it back, and this branch would
# say "nothing to release" and exit 0 — leaving a release that never reached
# origin and reporting success for it. So the local tag is confirmed present on
# origin before the no-op is believed. This costs one `git ls-remote`, which is
# why the preview above returns before reaching it.

if [ "$TAG" = "$LATEST" ]; then
  if git ls-remote --tags origin "refs/tags/$LATEST" | grep -q "$LATEST"; then
    echo "Nothing to release — derived version equals the current tag ($LATEST)."
    echo "Only conventional commits (feat:, fix:, ...) derive a new version."
    echo "Nothing was created."
    exit 0
  fi

  echo "error: tag $LATEST exists locally but NOT on origin" >&2
  echo "hint: a previous release run created the tag and failed before pushing" >&2
  echo "      it, so this release was never published." >&2
  echo "hint: push it and create the Release object:" >&2
  echo "        git push origin $LATEST" >&2
  echo "        bash infra/scripts/gitlab-release.sh $LATEST <notes-file>" >&2
  echo "hint: or discard it and start over: git tag -d $LATEST" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 4. Major-version guard
# ---------------------------------------------------------------------------
#
# Keyed on the SHAPE of the derived version, not on commit text, so it holds
# before and after 1.0. cliff.toml's `breaking_always_bump_major = false` is
# retained as belt and braces but is INERT once the major reaches 1 — verified:
# at v1.0.0 a `feat!:` still derives v2.0.0. This guard is what survives.
#
# CONFIRM_VERSION must equal the derived tag exactly rather than being a
# boolean, so a stale confirmation fails closed: if history moves between the
# refusal and the retry, the derived version changes and the old value no longer
# matches.

if [ "$LATEST" != "none" ]; then
  new_major=${TAG#v};    new_major=${new_major%%.*}
  old_major=${LATEST#v}; old_major=${old_major%%.*}

  if [ "$new_major" -gt "$old_major" ] && [ "${CONFIRM_VERSION:-}" != "$TAG" ]; then
    echo "error: this release changes the MAJOR version ($LATEST -> $TAG)" >&2
    echo "hint: re-run with CONFIRM_VERSION=$TAG" >&2
    echo "hint: nothing was created. Read the notes with PREVIEW=1 first if you" >&2
    echo "      did not expect a major bump." >&2
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 5. Tag hygiene
# ---------------------------------------------------------------------------
#
# Every local release tag must point at the same object as origin's tag of the
# same name.
#
# This is a reachable state, not a hypothetical one. The GitHub mirror push
# amends the release commit, and an earlier implementation force-moved the tag in
# the invoking clone, so any clone that ran a release under it carries the
# disagreement. A disagreeing tag poisons both computations the release path
# depends on: version derivation reads the wrong base (`git describe` returns the
# previous tag) and any publish range resolves against the wrong commit.
#
# Near-tautological in CI, which fetches --tags --force into a fresh clone. It
# earns its lines locally, where the failure is silent.
check_tag_hygiene() {
  local ref local_sha origin_sha tag disagreements=0

  while IFS=$'\t' read -r origin_sha ref; do
    tag="${ref#refs/tags/}"
    # Peeled entries (refs/tags/<name>^{}) restate the annotated tag's target;
    # comparing the tag object itself is what matters here.
    [ "${tag%^\{\}}" = "$tag" ] || continue

    # A tag that exists on origin but not locally is not a disagreement — there
    # is nothing local to be wrong. Only a name present on BOTH sides can
    # disagree.
    local_sha=$(git rev-parse --verify --quiet "refs/tags/$tag") || continue

    if [ "$local_sha" != "$origin_sha" ]; then
      echo "error: local tag $tag disagrees with origin" >&2
      echo "  local:  $local_sha" >&2
      echo "  origin: $origin_sha" >&2
      disagreements=$((disagreements + 1))
    fi
  done < <(git ls-remote --tags origin | grep -E 'refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$' || true)

  if [ "$disagreements" -gt 0 ]; then
    echo "hint: repair this clone with: git fetch origin --tags --force" >&2
    echo "hint: nothing was created." >&2
    exit 1
  fi

  echo "ok: local release tags agree with origin"
}

check_tag_hygiene

# ---------------------------------------------------------------------------
# 6. Tag absence — the double-tag guard
# ---------------------------------------------------------------------------
#
# Checked on BOTH sides. A local-only tag would make `git tag -a` fail with a
# less informative message; an origin-side tag means the version is already
# released and this run must not proceed.

if git rev-parse --verify --quiet "refs/tags/$TAG" >/dev/null; then
  echo "error: tag $TAG already exists locally" >&2
  echo "hint: if it was created by a failed run, delete it (git tag -d $TAG)" >&2
  echo "      and re-run. If it exists on origin too, $TAG is already released." >&2
  exit 1
fi

if git ls-remote --tags origin "refs/tags/$TAG" | grep -q "$TAG"; then
  echo "error: tag $TAG already exists on origin — nothing to release" >&2
  echo "hint: $TAG has already been released. If the GitLab Release object is" >&2
  echo "      missing but the tag exists, run gitlab-release.sh directly:" >&2
  echo "        bash infra/scripts/gitlab-release.sh $TAG <notes-file>" >&2
  exit 1
fi

echo "Releasing $TAG (current: $LATEST)"

# ---------------------------------------------------------------------------
# 7. Notes
# ---------------------------------------------------------------------------
#
# --tag stamps the heading as "## [X.Y.Z] - <date>". Without it the notes are
# headed "## [Unreleased]", which is wrong on a tag that names a version — and
# the publish path's heading assertion looks for "## [".
#
# Generated HERE, from current history. There is no committed changelog to read
# from, and generating fresh is what makes the published notes complete.

git-cliff --unreleased --tag "$TAG" --strip all > /tmp/release-notes.md

# Asserted rather than trusted: git-cliff exits 0 when the range resolves to
# nothing that cliff.toml groups, emitting output with no version heading.
if ! grep -q '^## \[' /tmp/release-notes.md; then
  echo "error: generated notes for $TAG contain no version heading" >&2
  echo "hint: .github/workflows/release.yml requires a '## [' heading in the tag" >&2
  echo "      annotation. Refusing to create a tag that would break the public" >&2
  echo "      release path. Nothing was created." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 8. Tag, push, publish internally
# ---------------------------------------------------------------------------
#
# `--cleanup=verbatim -F` is LOAD-BEARING, not stylistic. Git's default cleanup
# mode strips #-leading lines as comments and reflows content — and EXITS 0 while
# doing it, so the loss is silent. The public side
# (.github/workflows/release.yml) reads this annotation and requires it to
# contain "## [" headings. verbatim also preserves the two-space nested
# indentation cliff.toml produces, which is why its `trim = false` is mandatory
# for the same reason. Change either and the public release notes silently lose
# structure.

git tag -a "$TAG" --cleanup=verbatim -F /tmp/release-notes.md
git push origin "$TAG"

bash infra/scripts/gitlab-release.sh "$TAG" /tmp/release-notes.md

echo ""
echo "Released $TAG internally. Nothing was published to GitHub."
echo "To publish this tag publicly, run the 'github:release' job — its first run"
echo "without CONFIRM_TAG is a dry run that prints the value to re-run with."
