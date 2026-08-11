#!/usr/bin/env bash
# Prepare a release for review: regenerate CHANGELOG.md on a release/vX.Y.Z
# branch and open a merge request. Creates NO tag and NO GitLab Release.
#
# Usage: infra/scripts/release-prepare.sh [major]
#
#   (no argument)  ordinary release — minor or patch, derived from history
#   major          major release — requires CONFIRM_VERSION to match
#
# Why an MR instead of tagging directly: tags are the one artifact in this
# pipeline that cannot be cleanly retracted, and until now nobody saw the release
# notes in reviewable form before one existed. At v0.2.0 the committed
# CHANGELOG.md still read "## [Unreleased]" while the tag and the published
# Release both said 0.2.0, because regenerating it was an optional step someone
# had to remember. Here the changelog IS the merge request, so it cannot be
# skipped.
#
# This script pushes ONLY to a release/*-prefixed branch. It never pushes to the
# default branch, on any path.

set -euo pipefail

BUMP_MODE="${1:-}"

if [ -n "$BUMP_MODE" ] && [ "$BUMP_MODE" != "major" ]; then
  echo "error: unknown bump mode: $BUMP_MODE" >&2
  echo "hint: usage: release-prepare.sh [major]" >&2
  exit 1
fi

# shellcheck source=infra/scripts/changelog-lib.sh
. "$(dirname "$0")/changelog-lib.sh"

DEFAULT_BRANCH="${CI_DEFAULT_BRANCH:-main}"

# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------

# CI_COMMIT_BRANCH first, and it is not a nicety: a GitLab runner checks out a
# DETACHED HEAD ("Checking out 76097c5a as detached HEAD (ref is main)"), so
# `rev-parse --abbrev-ref HEAD` returns the literal string "HEAD" in every CI run
# and the guard below rejected its own release:prepare job. CI_COMMIT_BRANCH
# carries the branch the pipeline ran for, which is what the guard means to ask.
#
# Trusting it does not weaken the guard: the job rule already gates on
# $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH, and GitLab sets the variable, not the
# script. Locally it is unset and the rev-parse form applies unchanged.
#
# The other release paths never tripped this because they ask no branch question —
# release-run.sh tags HEAD, which works detached.
current_branch="${CI_COMMIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"
if [ "$current_branch" != "$DEFAULT_BRANCH" ]; then
  # A leftover release/* checkout is the expected state after a run that failed
  # at the push, so recover from it rather than dead-ending: the release branch
  # is machine-authored and carries nothing that is not regenerated below.
  case "$current_branch" in
    release/*)
      echo "note: on $current_branch, left over from an earlier run — returning to $DEFAULT_BRANCH"
      if ! git checkout "$DEFAULT_BRANCH" >/dev/null 2>&1; then
        echo "error: could not switch to $DEFAULT_BRANCH from $current_branch" >&2
        echo "hint: commit or stash your changes, then re-run." >&2
        exit 1
      fi
      ;;
    *)
      echo "error: release preparation must run from $DEFAULT_BRANCH (on $current_branch)" >&2
      echo "hint: the release branch is cut FROM the default branch. Switch with:" >&2
      echo "        git checkout $DEFAULT_BRANCH && git pull" >&2
      exit 1
      ;;
  esac
fi

# ---------------------------------------------------------------------------
# Derive the version. There is no VERSION file — the version is derived from
# Conventional Commit history, never supplied.
# ---------------------------------------------------------------------------

if [ "$BUMP_MODE" = "major" ]; then
  TAG=$(git-cliff --bump major --bumped-version 2>/dev/null || echo '')
else
  TAG=$(git-cliff --bumped-version 2>/dev/null || echo '')
fi

if [ -z "$TAG" ]; then
  echo "error: could not derive a version to prepare" >&2
  echo "hint: is git-cliff installed and is cliff.toml present?" >&2
  echo "      brew install git-cliff" >&2
  exit 1
fi

LATEST=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")

# The idempotent no-op. Derivation returns the current tag when nothing in the
# window affects the version, so this is a reliable "nothing to do" signal — and
# it exits 0, deliberately. A caller (human or automated) can run this
# unconditionally and only get a branch when there is genuinely something to
# release.
if [ "$TAG" = "$LATEST" ]; then
  echo "Nothing to release — derived version equals the current tag ($LATEST)."
  echo "Only conventional commits (feat:, fix:, ...) derive a new version."
  echo ""
  echo "Nothing was created: no branch, no commit, no merge request, no tag."
  exit 0
fi

# ---------------------------------------------------------------------------
# Major gate, BEFORE anything is created. A gate that fires after the branch
# exists is not a gate.
# ---------------------------------------------------------------------------

if [ "$BUMP_MODE" = "major" ] && [ "${CONFIRM_VERSION:-}" != "$TAG" ]; then
  echo "error: preparing a major release requires explicit confirmation" >&2
  echo "would prepare: $TAG" >&2
  echo "hint: re-run with CONFIRM_VERSION=$TAG" >&2
  exit 1
fi

BRANCH="release/$TAG"

# Preparation must not race a release that already happened.
if git rev-parse --verify --quiet "refs/tags/$TAG" >/dev/null; then
  echo "error: tag $TAG already exists locally — nothing to prepare" >&2
  echo "hint: $TAG has already been released. Land more commits first, or if this" >&2
  echo "      clone is stale: git fetch origin --tags --force" >&2
  exit 1
fi

if git ls-remote --tags origin "refs/tags/$TAG" 2>/dev/null | grep -q "refs/tags/$TAG"; then
  echo "error: tag $TAG already exists on origin — nothing to prepare" >&2
  echo "hint: someone released $TAG already. Refresh with:" >&2
  echo "        git fetch origin --tags --force" >&2
  exit 1
fi

echo "Preparing $TAG (current: $LATEST)"
echo ""

# ---------------------------------------------------------------------------
# Build the release branch: one commit, CHANGELOG.md only.
# ---------------------------------------------------------------------------

# `checkout -B` rather than `-b`: on a re-run after a failed push, the local
# branch already exists and `-b` would fail with an opaque error.
git checkout -B "$BRANCH" >/dev/null 2>&1

if ! generate_changelog "$TAG" CHANGELOG.md; then
  echo "error: could not generate CHANGELOG.md for $TAG" >&2
  echo "hint: does the floor tag $CHANGELOG_FLOOR exist locally? A shallow clone" >&2
  echo "      may not have it — CI sets GIT_DEPTH: 0 for this reason." >&2
  git checkout "$DEFAULT_BRANCH" >/dev/null 2>&1 || true
  exit 1
fi

# A generation that produced no version headings is a silent failure: git-cliff
# exits 0 and emits a bare header when the range resolves to nothing.
if ! grep -q '^## \[' CHANGELOG.md; then
  echo "error: generated CHANGELOG.md for $TAG contains no version heading" >&2
  echo "hint: the range refs/tags/$CHANGELOG_FLOOR.. resolved to no commits that" >&2
  echo "      cliff.toml groups. git-cliff exits 0 in this case, so this is" >&2
  echo "      asserted rather than trusted." >&2
  git checkout -- CHANGELOG.md 2>/dev/null || true
  git checkout "$DEFAULT_BRANCH" >/dev/null 2>&1 || true
  exit 1
fi

# Stage CHANGELOG.md alone. `commit -am` would sweep in any other dirty file, and
# the release commit must touch exactly one path.
git add CHANGELOG.md

# Compare the STAGED content against HEAD, not the working tree against HEAD.
# `git diff -- CHANGELOG.md` reports no change for an UNTRACKED file, because
# diff only considers tracked paths — so on a repository whose changelog does not
# yet exist, the working-tree form of this check wrongly concludes "already
# current" and refuses to prepare anything. Staging first makes a new file a
# visible addition.
if git diff --cached --quiet HEAD -- CHANGELOG.md 2>/dev/null; then
  echo "error: CHANGELOG.md is already current for $TAG — nothing to commit" >&2
  echo "" >&2
  echo "The committed changelog already matches what $TAG will publish, so a" >&2
  echo "changelog-only release branch would be empty." >&2
  echo "hint: this usually means the changelog was regenerated and committed to" >&2
  echo "      $DEFAULT_BRANCH directly, bypassing the review flow. $TAG is ready" >&2
  echo "      to release as-is — run the 'release' job rather than this one." >&2
  git checkout "$DEFAULT_BRANCH" >/dev/null 2>&1 || true
  exit 1
fi

# `chore(release):` — cliff.toml skips ^chore, so the release ceremony produces
# no entry in the notes it generates, under either merge method.
git commit --quiet -m "chore(release): $TAG" \
  -m "Regenerate CHANGELOG.md for $TAG. Generated by release-prepare.sh; do not hand-edit."

# Assert what was actually committed rather than trusting it.
changed_files=$(git diff-tree --no-commit-id --name-only -r HEAD)
changed_count=$(printf '%s\n' "$changed_files" | grep -c . || true)
if [ "$changed_count" -ne 1 ] || [ "$changed_files" != "CHANGELOG.md" ]; then
  echo "error: the release commit must touch exactly CHANGELOG.md" >&2
  echo "  touched: $changed_files" >&2
  echo "hint: the working tree had other staged changes. Nothing was pushed." >&2
  exit 1
fi

echo "ok: committed chore(release): $TAG on $BRANCH (CHANGELOG.md only)"

# ---------------------------------------------------------------------------
# Idempotency: has this branch already been pushed with this exact content?
# ---------------------------------------------------------------------------

remote_sha=$(git ls-remote --heads origin "refs/heads/$BRANCH" 2>/dev/null | cut -f1)

if [ -n "$remote_sha" ]; then
  echo "note: $BRANCH already exists on origin ($remote_sha)"
  # Compare TREES, not commit SHAs: a re-run produces a different commit SHA
  # (different timestamp) for identical content. If the content matches, the
  # branch is already prepared and there is nothing to do.
  if remote_tree=$(git rev-parse --quiet --verify "$remote_sha^{tree}" 2>/dev/null) \
     && [ "$remote_tree" = "$(git rev-parse 'HEAD^{tree}')" ]; then
    echo ""
    echo "ok: $BRANCH is already prepared with identical content — nothing to do."
    echo "    No tag was created."
    # Leave the clone where the operator started it, as every other exit does.
    git checkout "$DEFAULT_BRANCH" >/dev/null 2>&1 || true
    exit 0
  fi
  echo "      content differs — the branch will be updated (--force-with-lease)."
fi

# ---------------------------------------------------------------------------
# Push, and ask GitLab to open the merge request via push options.
# ---------------------------------------------------------------------------

# Guard, not decoration: every push in this script must target release/*. This
# catches a future edit that reintroduces a default-branch push.
case "$BRANCH" in
  release/*) : ;;
  *)
    echo "error: refusing to push non-release branch '$BRANCH'" >&2
    exit 1
    ;;
esac

# The MR title IS the release marker, not decoration.
#
# release:auto detects a release merge by looking for a `chore(release): ` commit
# subject in the range since the newest tag. Under a merge-commit merge that
# subject arrives via the branch's own commit. Under a SQUASH merge the branch's
# commits collapse into one whose subject GitLab defaults to the MERGE REQUEST
# TITLE — so if the title were "Release v0.3.0", a squashed release would carry no
# marker and would not be detected.
#
# Setting the title to the marker makes detection work under BOTH merge methods by
# construction rather than by luck. `^chore` is skipped by cliff.toml, so this
# still contributes no changelog entry either way.
MR_TITLE="chore(release): $TAG"
# Literal newlines are REJECTED in push option values with
# "fatal: push options must not have new line characters". GitLab converts a
# two-character \n into a real newline, so the description is built with escapes.
MR_DESC="Regenerated \`CHANGELOG.md\` for **$TAG** (derived from Conventional Commit history).\n\nOpened by \`release-prepare.sh\`. **Merging this tags $TAG and creates the GitLab Release automatically** — review the notes before merging.\n\nNothing is published to GitHub by merging; that remains a separate confirmed act.\n\nDo not change the MR title: it is the marker the automatic release job detects.\n\nSee \`.gitlab/merge_request_templates/release.md\` for what to review."

set +e
push_output=$(git push --force-with-lease \
  -o merge_request.create \
  -o merge_request.target="$DEFAULT_BRANCH" \
  -o merge_request.title="$MR_TITLE" \
  -o merge_request.description="$MR_DESC" \
  -o merge_request.remove_source_branch \
  origin "$BRANCH" 2>&1)
push_status=$?
set -e

echo "$push_output"

# A receiver that does not understand push options rejects the WHOLE push, not
# just the options — "fatal: the receiving end does not support push options".
# Getting the branch pushed matters more than getting the MR opened, so retry
# without them. The MR then costs one manual click, which is the documented
# fallback rather than a failure.
if [ $push_status -ne 0 ] && printf '%s' "$push_output" | grep -q 'does not support push options'; then
  echo ""
  echo "note: this remote does not support push options — retrying the push"
  echo "      without them. The branch is what matters; the merge request will"
  echo "      have to be opened by hand."
  set +e
  push_output=$(git push --force-with-lease origin "$BRANCH" 2>&1)
  push_status=$?
  set -e
  echo "$push_output"
fi

if [ $push_status -ne 0 ]; then
  echo "" >&2
  echo "error: could not push $BRANCH to origin" >&2
  echo "hint: a job-token push requires the project setting" >&2
  echo "      Settings > CI/CD > Job token permissions >" >&2
  echo "      'Allow Git push requests to this project's repository' (off by" >&2
  echo "      default, needs Maintainer/Owner, requires GitLab 17.2+)." >&2
  echo "      It also requires release/* to be UNPROTECTED." >&2
  echo "      If the setting is unavailable, the documented fallback is a project" >&2
  echo "      access token with 'api' scope as a masked CI variable — see" >&2
  echo "      docs developer-docs/internal/operations/runbooks/release-prerequisites.md" >&2
  echo "note: the commit exists locally on $BRANCH. Nothing was lost — re-running" >&2
  echo "      this script after fixing the cause is safe." >&2
  # Return the clone to the default branch, or a re-run trips the branch guard
  # before it can report anything useful.
  git checkout "$DEFAULT_BRANCH" >/dev/null 2>&1 || true
  exit 1
fi

echo ""
echo "ok: pushed $BRANCH to origin"

# GitLab echoes the created or existing MR URL on the push's remote output. Look
# for it rather than assuming push options worked — whether they are honoured for
# a JOB-TOKEN push is not documented, so this is observed rather than trusted.
mr_url=$(printf '%s\n' "$push_output" | grep -oE 'https?://[^[:space:]]*/-/merge_requests/[0-9]+' | head -1 || true)

if [ -n "$mr_url" ]; then
  echo "ok: merge request: $mr_url"
else
  # The branch is pushed and safe. Only the MR is missing, which costs one click.
  new_mr_url=""
  if [ -n "${CI_PROJECT_URL:-}" ]; then
    new_mr_url="$CI_PROJECT_URL/-/merge_requests/new?merge_request%5Bsource_branch%5D=$BRANCH"
  fi
  echo ""
  echo "note: the push did not report a merge request URL."
  echo "      The branch IS pushed — nothing was lost. Open the MR by hand:"
  if [ -n "$new_mr_url" ]; then
    echo "        $new_mr_url"
  else
    echo "        <project URL>/-/merge_requests/new?merge_request[source_branch]=$BRANCH"
  fi
  echo "      Target $DEFAULT_BRANCH. This is the documented fallback for an"
  echo "      instance that does not honour MR-creating push options with a job"
  echo "      token; it costs one manual step and no new credential."
fi

# Leave the operator's clone where they started, so a local run is not a trap.
git checkout "$DEFAULT_BRANCH" >/dev/null 2>&1 || true

echo ""
echo "Prepared $TAG for review."
echo "  branch:  $BRANCH (one commit, CHANGELOG.md only)"
echo "  NO TAG was created by this job, and nothing was published."
echo ""
echo "Next: review the notes, then merge the merge request. MERGING TAGS $TAG"
echo "      and creates the GitLab Release automatically (release:auto)."
echo "      Publishing to GitHub stays separate and confirmation-gated."
