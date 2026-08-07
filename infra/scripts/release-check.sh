#!/usr/bin/env bash
set -euo pipefail

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
