#!/usr/bin/env bash
set -euo pipefail

# Three assertions, run BEFORE a tag is created: tag hygiene, derived-equals-
# requested, and CHANGELOG.md matches the generated output.
#
# The first two are HARD in every path. Neither can be tripped by somebody else's
# merge — a disagreeing tag is a broken clone and a mismatched version is a
# mistaken request, so a failure is always a real problem with this release.
#
# The third honours ADVISORY_CHANGELOG=1 (set only by the automatic path), where
# a mismatch usually means ordinary team activity rather than a defect. The
# reasoning is at that assertion.

# Tag hygiene: every local release tag must point at the same commit as origin's
# tag of the same name.
#
# This is a reachable state, not a hypothetical one. The GitHub mirror push amends
# the release commit and then force-moves the tag locally (github-push.sh), so any
# clone that has run a release carries the disagreement. A disagreeing tag poisons
# both computations the release path depends on: version derivation reads the wrong
# base (`git describe` returns the previous tag), and any publish range resolves
# against the wrong commit.
check_tag_hygiene() {
  local ref local_sha origin_sha tag disagreements=0

  while IFS=$'\t' read -r origin_sha ref; do
    tag="${ref#refs/tags/}"
    # Peeled entries (refs/tags/<name>^{}) restate the annotated tag's target;
    # comparing the tag object itself is what matters here.
    [ "${tag%^\{\}}" = "$tag" ] || continue

    # A tag that exists on origin but not locally is not a disagreement — there is
    # nothing local to be wrong. Only a name present on BOTH sides can disagree.
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
    exit 1
  fi

  echo "ok: local release tags agree with origin"
}

check_tag_hygiene

# The tag about to be released must equal the version derived from Conventional
# Commit history. There is no VERSION file to compare against — the version is
# derived, not stamped, so the only thing worth asserting is that the tag being
# created agrees with what the history says it should be.
#
# This check runs BEFORE the tag is created, for two reasons. It is the only
# point at which the assertion can fail without leaving a wrong tag behind. And
# `--bumped-version` reports the tag on HEAD once one exists, so after tagging
# the comparison would trivially pass against any value.
tag="${1:-${CI_COMMIT_TAG:-}}"

# Optional bump mode, matching what the caller derived with. The major release
# job derives with `--bump major`, so the check must derive the same way or it
# would compare a major tag against a minor derivation and always fail.
bump_mode="${2:-}"

if [ -z "$tag" ]; then
  echo "error: no tag supplied to check" >&2
  echo "hint: usage: release-check.sh <tag> [major], or set CI_COMMIT_TAG" >&2
  exit 1
fi

if git rev-parse --verify --quiet "refs/tags/$tag" >/dev/null; then
  echo "error: tag $tag already exists — this check must run BEFORE tagging" >&2
  echo "hint: once the tag exists, derivation reports it back and the comparison" >&2
  echo "      cannot fail. Delete it (git tag -d $tag) and re-run the release job." >&2
  exit 1
fi

if [ "$bump_mode" = "major" ]; then
  derived=$(git-cliff --bump major --bumped-version 2>/dev/null || echo '')
else
  derived=$(git-cliff --bumped-version 2>/dev/null || echo '')
fi

if [ -z "$derived" ]; then
  echo "error: could not derive a version to compare against $tag" >&2
  echo "hint: is git-cliff installed and is cliff.toml present?" >&2
  exit 1
fi

if [ "$derived" != "$tag" ]; then
  echo "error: tag ($tag) does not match the derived version ($derived)" >&2
  echo "  requested: $tag" >&2
  echo "  derived:   $derived" >&2
  echo "hint: the version is derived from commit history, not chosen. Release" >&2
  echo "      $derived instead, or add the commits that would justify $tag." >&2
  exit 1
fi

echo "ok: $tag matches the derived version"

# ---------------------------------------------------------------------------
# CHANGELOG.md is generated — assert it was regenerated for THIS tag
# ---------------------------------------------------------------------------
#
# The file is a build output of `git-cliff "refs/tags/$CHANGELOG_FLOOR.."`, not a
# hand-maintained document.
#
# It IS written in CI, by release-prepare.sh, onto a release/* branch that a human
# reviews and merges. What CI cannot do is write it directly to the trunk: a job
# token cannot push to a PROTECTED branch, and main is protected. That single fact
# is what shapes the whole flow — the release branch is writable and the trunk is
# not, so the changelog reaches main through a reviewed merge rather than a
# commit-back.
#
# (An earlier version of this comment claimed CI_JOB_TOKEN cannot push at all.
# That generalisation was wrong: branch push with a job token is generally
# available as of GitLab 18.4, subject to a project setting. Only the
# protected-branch half of the claim was ever true.)
#
# Before that flow existed, the committed file went stale the moment someone
# released without regenerating it — exactly what happened at v0.2.0, where the
# file still read "## [Unreleased]" while the tag and the published Release both
# said 0.2.0. This assertion is why that cannot recur silently.
#
# This compares the committed file against a fresh generation for $tag, ignoring
# only the release date in version headings (see normalise_release_dates below).
# It is not a nuisance check: it can only fail when the file genuinely does not
# match what this release will publish, and the fix is one command. It runs
# before tagging, so a failure leaves no tag behind.
# CHANGELOG_FLOOR and the generation command itself live in one shared place, so
# that what this script VERIFIES cannot drift from what release-prepare.sh and
# release.mk WRITE.
# shellcheck source=infra/scripts/changelog-lib.sh
. "$(dirname "$0")/changelog-lib.sh"

if [ ! -f CHANGELOG.md ]; then
  echo "error: CHANGELOG.md is missing" >&2
  echo "hint: make -f infra/scripts/release.mk release-changelog VERSION=${tag#v}" >&2
  exit 1
fi

expected="$(mktemp)"
expected_norm="$(mktemp)"
committed_norm="$(mktemp)"
# One trap for all three. A second `trap ... EXIT` would silently replace this
# one rather than adding to it, leaking whichever file the first trap covered.
trap 'rm -f "$expected" "$expected_norm" "$committed_norm"' EXIT

# The release date is normalised out of version headings before comparing.
#
# For an UNRELEASED version, cliff.toml's heading template stamps the moment of
# generation, not the commit date and not the tag date:
#
#   ## [{{ version ... }}] - {{ timestamp | date(format="%Y-%m-%d") }}
#
# So a changelog generated on one day and verified on the next differs by one
# line, and a byte-for-byte comparison fails on it. That is a false failure: the
# date is the one field in the heading that cannot be verified before the tag
# exists, because there is nothing yet to read it from. Once the tag exists,
# git-cliff reads the date from the tag and it becomes stable.
#
# The pattern is anchored at both ends and requires the full
# "## [X.Y.Z] - YYYY-MM-DD" shape, so it rewrites version headings and nothing
# else — not a bullet that mentions a date, not a body line containing "## [".
# The version itself is NOT normalised, so a changelog generated for the wrong
# version still fails. `sed -E` rather than `-r`: `-E` is POSIX and works under
# both GNU sed (the CI image) and BSD sed (an operator's macOS workstation).
#
# Coupled to cliff.toml's `body` heading template — if that heading format
# changes, this pattern must change with it.
normalise_release_dates() {
  sed -E 's/^(## \[[0-9]+\.[0-9]+\.[0-9]+\]) - [0-9]{4}-[0-9]{2}-[0-9]{2}$/\1 - <date>/' "$1"
}

if ! generate_changelog "$tag" "$expected"; then
  echo "error: could not generate the expected CHANGELOG for $tag" >&2
  echo "hint: does the floor tag $CHANGELOG_FLOOR exist locally? A shallow clone" >&2
  echo "      may not have it — the release job sets GIT_DEPTH: 0 for this reason." >&2
  exit 1
fi

# A generation that produced no version headings is a silent failure, not a pass:
# git-cliff exits 0 and emits a bare header when the range resolves to nothing.
if ! grep -q '^## \[' "$expected"; then
  echo "error: generated CHANGELOG for $tag contains no version heading" >&2
  echo "hint: the range refs/tags/$CHANGELOG_FLOOR.. resolved to no commits that" >&2
  echo "      cliff.toml groups. git-cliff exits 0 in this case, so this is" >&2
  echo "      asserted rather than trusted." >&2
  exit 1
fi

normalise_release_dates "$expected" > "$expected_norm"
normalise_release_dates CHANGELOG.md > "$committed_norm"

if ! diff -q "$expected_norm" "$committed_norm" >/dev/null 2>&1; then
  # ADVISORY_CHANGELOG: warn instead of failing. Set ONLY by the automatic
  # release path, and the asymmetry is deliberate.
  #
  # In the MANUAL path the operator regenerated the changelog moments ago, so a
  # mismatch means they got it wrong — a real error, worth catching before a tag
  # exists.
  #
  # In the AUTOMATIC path a mismatch usually means somebody ELSE merged something
  # while the release was under review. That is ordinary team activity, not a
  # defect in the release, and failing on it would block releases for a reason
  # the releaser cannot control — which is how you get an assertion operators
  # learn to bypass.
  #
  # Nothing is lost by warning here: the notes attached to the tag are generated
  # fresh from history at release time (release-run.sh), so the PUBLISHED notes
  # are complete regardless. Only the committed file is briefly behind, and it is
  # regenerated in full from CHANGELOG_FLOOR at the next release, which recovers
  # the missing entry automatically.
  #
  # The other two assertions stay HARD in both paths: tag hygiene and
  # derived-equals-requested cannot be tripped by someone else's merge, so a
  # failure there is always a real problem.
  if [ "${ADVISORY_CHANGELOG:-}" = "1" ]; then
    echo "warning: CHANGELOG.md does not match what $tag will publish" >&2
    echo "" >&2
    { diff "$expected" CHANGELOG.md || true; } | head -40 >&2
    echo "" >&2
    echo "note: this is ADVISORY in the automatic release path and does NOT block" >&2
    echo "      the release. The most likely cause is a commit merged to the" >&2
    echo "      default branch while this release was under review." >&2
    echo "note: the notes attached to the tag are generated fresh from history, so" >&2
    echo "      the PUBLISHED notes are complete. Only the committed file is" >&2
    echo "      behind, and the next release regenerates it in full — the missing" >&2
    echo "      entry reappears then, in this version's section." >&2
    echo "hint: to reconcile it now: " >&2
    echo "        make -f infra/scripts/release.mk release-changelog VERSION=${tag#v}" >&2
    echo "" >&2
    echo "ok: CHANGELOG.md check completed with warnings (advisory mode)"
    exit 0
  fi

  echo "error: CHANGELOG.md does not match what $tag will publish" >&2
  echo "" >&2
  # The UNNORMALISED diff, deliberately: an operator debugging a mismatch needs
  # the real line content. A diff full of "- <date>" placeholders would obscure
  # the line they actually need to see.
  { diff "$expected" CHANGELOG.md || true; } | head -40 >&2
  echo "" >&2
  echo "hint: CHANGELOG.md is GENERATED, not hand-edited. Regenerate and commit it:" >&2
  echo "        make -f infra/scripts/release.mk release-changelog VERSION=${tag#v}" >&2
  echo "        git commit -am 'chore: release $tag'" >&2
  echo "      To change the WORDING, amend the commit body — prose lives in commit" >&2
  echo "      bodies, which cliff.toml renders under each bullet. To add a missing" >&2
  echo "      entry, add an empty commit carrying the prose:" >&2
  echo "        git commit --allow-empty -m 'feat(scope): subject' -m 'body...'" >&2
  echo "hint: the release DATE in a version heading is excluded from this" >&2
  echo "      comparison, so a date difference is not what failed here — look" >&2
  echo "      for a content or version difference in the diff above." >&2
  exit 1
fi

echo "ok: CHANGELOG.md matches the generated output for $tag"
