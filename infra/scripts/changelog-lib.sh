#!/usr/bin/env bash
# Shared changelog generation. Sourced, not executed.
#
# Every path that writes or verifies CHANGELOG.md generates it through this file:
# release-prepare.sh (writes it), release-check.sh (verifies it), and release.mk
# (regenerates it locally). The release path asserts that the committed file
# matches a fresh generation byte-for-byte, so three hand-synchronised copies of
# the same git-cliff invocation is precisely the mechanism by which that
# assertion starts failing for no real reason. There is one copy, here.

# CHANGELOG_FLOOR is the cutover: everything AFTER it is generated from commit
# history, everything at or before it is frozen text in cliff.toml's `footer`.
#
# Conventional Commits were adopted in v0.1.6, so generating across that boundary
# drops v0.1.1 entirely and reduces v0.1.3 to a bare heading — verified. Do not
# lower this without first moving the corresponding sections into the footer.
CHANGELOG_FLOOR="${CHANGELOG_FLOOR:-v0.1.4}"
export CHANGELOG_FLOOR

# generate_changelog <tag> <outfile>
#
# Writes the changelog for <tag> to <outfile>. Returns non-zero if git-cliff
# fails; the caller owns the error message, because what a failure MEANS differs
# by caller (a missing floor tag is a shallow-clone problem in CI and a fetch
# problem locally).
generate_changelog() {
  local tag="${1:?generate_changelog: tag required}"
  local outfile="${2:?generate_changelog: outfile required}"

  git-cliff "refs/tags/$CHANGELOG_FLOOR.." --tag "$tag" -o "$outfile" 2>/dev/null
}
