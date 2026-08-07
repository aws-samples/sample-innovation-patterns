#!/usr/bin/env bash
# Publish a chosen internal tag to the public GitHub mirror, with release notes
# covering every change since the last GitHub publish.
#
# Usage:
#   internal/release/publish-github.sh [--dry-run] [TAG]
#   TAG=v0.4.0 internal/release/publish-github.sh --dry-run
#
# Stage 2 of a two-stage release. Stage 1 (the `release` GitLab job) cuts an
# internal tag and publishes nothing publicly; this publishes a chosen tag —
# including an older one — to GitHub.
#
# Publishing withholds only TAGS and RELEASE OBJECTS, never code: the mirror
# amends the tip and force-pushes main, so a skipped release's code lands
# publicly anyway. That is what makes cumulative notes correctness rather than
# courtesy — a gap in the public tag sequence describes real published code that
# no Release object currently documents.
#
# Four values are computed, each with a subtlety that breaks it if missed:
#
#   TAG    newest strict-semver tag on origin, or an explicit override.
#          Must filter to strict semver or a stray v0.9.9-rc1 wins.
#   FLOOR  newest strict-semver tag on github. Needs sort -V; plain sort ranks
#          v0.1.2 above v0.1.10 (verified).
#   NOTES  git-cliff FLOOR..TAG --strip all. GitHub supplies the floor's NAME;
#          the range must resolve against origin's commit for that name, because
#          GitHub's tag objects point at amended commits.
#   tree   EXCLUDE_PATHS applied in a throwaway worktree. The old
#          github-push.sh ran `git tag -f` in the operator's clone, which is
#          what corrupted local v0.1.7.

set -euo pipefail

DRY_RUN=false
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    -*) echo "error: unknown flag: $arg" >&2; exit 1 ;;
    *) ARGS+=("$arg") ;;
  esac
done

GITHUB_REMOTE="github"
GITHUB_REPO="git@github.com:aws-samples/sample-innovation-patterns.git"
ORIGIN_REMOTE="origin"
SEMVER_RE='^v[0-9]+\.[0-9]+\.[0-9]+$'

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# ---------------------------------------------------------------------------
# Internal-only paths
# ---------------------------------------------------------------------------

# Paths that stay in GitLab but must never ship to GitHub.
EXCLUDE_PATHS=(
  ".gitlab-ci.yml"
  ".gitlab"
  ".specify"
  "docs/docs/developer-docs/internal"
  "docs/docs/guides/releasing.md"
  "scripts/.gitignore"
  "internal"
)

# Asserted below. A quoting or separator defect that merges two entries into one
# silently reduces the number of paths filtered, so the count is checked rather
# than assumed. Update this when adding an entry above.
EXPECTED_EXCLUDE_COUNT=7

# Entries deliberately absent from the tracked tree. Everything NOT listed here
# must have been tracked in HEAD before the removal loop — otherwise a typo is
# indistinguishable from a successful removal, since both leave the path absent.
#
#   .specify                      on disk but git-ignored. Excluded as
#                                 belt-and-braces in case it is ever un-ignored.
#   docs/docs/guides/releasing.md has NEVER existed on disk. Retained to reserve
#                                 the name: a guide written at this exact path
#                                 would be silently stripped from the public
#                                 tree. Write builder release docs elsewhere.
INTENTIONALLY_ABSENT=(
  ".specify"
  "docs/docs/guides/releasing.md"
)

is_intentionally_absent() {
  local needle="$1" entry
  for entry in "${INTENTIONALLY_ABSENT[@]}"; do
    [ "$entry" = "$needle" ] && return 0
  done
  return 1
}

if [ "${#EXCLUDE_PATHS[@]}" -ne "$EXPECTED_EXCLUDE_COUNT" ]; then
  echo "error: EXCLUDE_PATHS holds ${#EXCLUDE_PATHS[@]} elements, expected $EXPECTED_EXCLUDE_COUNT" >&2
  echo "hint: a missing separator merges two entries into one, silently reducing" >&2
  echo "      what is filtered. Check quoting, or update EXPECTED_EXCLUDE_COUNT" >&2
  echo "      if an entry was added deliberately." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Tag and floor resolution
# ---------------------------------------------------------------------------

remote_semver_tags() {
  git ls-remote --tags "$1" 2>/dev/null \
    | awk '{print $2}' \
    | sed 's|^refs/tags/||' \
    | grep -E "$SEMVER_RE" \
    | sort -V
}

git remote add "$GITHUB_REMOTE" "$GITHUB_REPO" 2>/dev/null || true

TAG="${ARGS[0]:-${TAG:-}}"
if [ -z "$TAG" ]; then
  TAG="$(remote_semver_tags "$ORIGIN_REMOTE" | tail -1)"
  if [ -z "$TAG" ]; then
    echo "error: no strict-semver tag found on $ORIGIN_REMOTE" >&2
    exit 1
  fi
  echo "TAG not supplied — defaulting to the newest tag on $ORIGIN_REMOTE"
fi

if ! remote_semver_tags "$ORIGIN_REMOTE" | grep -qx "$TAG"; then
  echo "error: $TAG is not a strict-semver tag on $ORIGIN_REMOTE" >&2
  echo "hint: available tags:" >&2
  remote_semver_tags "$ORIGIN_REMOTE" | sed 's/^/        /' >&2
  exit 1
fi

# GitHub is the only authority on what GitHub already has. A marker file would be
# a second source of truth that can drift, and drift here means either
# republishing notes or silently dropping a version's worth of them.
FLOOR="$(remote_semver_tags "$GITHUB_REMOTE" | tail -1 || true)"

echo "TAG:   $TAG"
if [ -n "$FLOOR" ]; then
  echo "FLOOR: $FLOOR (newest tag already on $GITHUB_REMOTE)"
else
  echo "FLOOR: none — no semver tag on $GITHUB_REMOTE, notes will span full history"
fi

# The window must run forward. Publishing a tag at or below the floor would
# produce a backwards range, which git-cliff answers with an "Unreleased"
# section rather than an error — a plausible-looking body describing nothing.
#
# Note this is not the same as "publishing an older tag is unsupported": an
# older tag publishes fine as long as it is newer than what GitHub already has.
# What cannot be done is publishing BEHIND the public mirror, because the notes
# window for that is empty by definition and the mirror is already ahead.
if [ -n "$FLOOR" ] && [ "$TAG" = "$FLOOR" ]; then
  echo "error: $TAG is already the newest tag on $GITHUB_REMOTE — nothing to publish" >&2
  exit 1
fi

if [ -n "$FLOOR" ] && [ "$(printf '%s\n%s\n' "$TAG" "$FLOOR" | sort -V | tail -1)" = "$FLOOR" ]; then
  echo "error: $TAG is older than the newest tag already on $GITHUB_REMOTE ($FLOOR)" >&2
  echo "hint: the public mirror is already ahead of $TAG, so there is nothing since" >&2
  echo "      the last publish to describe. Publish a tag newer than $FLOOR." >&2
  exit 1
fi

# Make sure the local objects for both endpoints exist and agree with origin.
git fetch --quiet "$ORIGIN_REMOTE" --tags --force

# ---------------------------------------------------------------------------
# Cumulative notes
# ---------------------------------------------------------------------------

NOTES_FILE="$(mktemp)"
trap 'rm -f "$NOTES_FILE"' EXIT

# FLOOR supplies the NAME from GitHub; the range resolves against origin's commit
# for that name. GitHub's tag objects point at amended commits, so resolving the
# range there would span the wrong window or fail outright.
if [ -n "$FLOOR" ]; then
  if ! git rev-parse --verify --quiet "refs/tags/$FLOOR" >/dev/null; then
    echo "error: floor tag $FLOOR exists on $GITHUB_REMOTE but not locally" >&2
    echo "hint: git fetch $ORIGIN_REMOTE --tags --force" >&2
    exit 1
  fi
  git-cliff "refs/tags/$FLOOR".."refs/tags/$TAG" --strip all > "$NOTES_FILE"
else
  git-cliff --tag "$TAG" --strip all > "$NOTES_FILE"
fi

if [ ! -s "$NOTES_FILE" ]; then
  echo "error: generated notes are empty for $FLOOR..$TAG" >&2
  echo "hint: is $TAG newer than $FLOOR? Nothing to publish otherwise." >&2
  exit 1
fi

echo
echo "--- release notes ($FLOOR..$TAG, exclusive of the floor) ---"
cat "$NOTES_FILE"
echo "--- end release notes ---"
echo

# ---------------------------------------------------------------------------
# Divergence assertion
# ---------------------------------------------------------------------------

# Two things are load-bearing here.
#
# UNSHALLOW FIRST. .git/shallow may contain the mirror tip, in which case
# ancestry questions are answered from a truncated graph and FAIL CLOSED —
# reporting "not an ancestor" for commits that genuinely are ancestors. An
# assertion that always fails is worse than none: operators learn to bypass it.
#
# ASSERT ON CONTENT, NOT COMMIT IDENTITY. The mirror's commits are AMENDED
# versions of internal commits — different SHAs for identical content, by design.
# So "is this public commit an ancestor?" answers no for every mirror commit even
# when the mirror is perfectly reconciled. The real question is whether the
# mirror holds content the internal line lacks.
#
# --force-with-lease is NOT the guard: a fresh CI clone establishes its
# remote-tracking ref at whatever the remote holds, so the lease passes precisely
# when a fresh clone is used, which is always in CI.
assert_no_divergence() {
  if [ "$(git rev-parse --is-shallow-repository)" = "true" ]; then
    echo "unshallowing before reasoning about ancestry..."
    git fetch --quiet --unshallow "$ORIGIN_REMOTE" 2>/dev/null || git fetch --quiet --unshallow || true
  fi

  if ! git fetch --quiet "$GITHUB_REMOTE" main 2>/dev/null; then
    echo "note: $GITHUB_REMOTE/main not fetchable (likely first publish) — skipping divergence check"
    return 0
  fi

  # Paths the mirror has that the internal line does not.
  #
  # Deliberate removals must be excluded or this fires on every run: EXCLUDE_PATHS
  # is stripped on every publish, and files removed by an internal commit are
  # absent internally by design. Both are "the mirror is behind", not divergence.
  # An assertion that always fails teaches operators to bypass it, so the
  # filtering here is the difference between a real guard and a nuisance.
  local candidates orphans=""
  candidates="$(comm -23 \
    <(git ls-tree -r FETCH_HEAD --name-only | sort) \
    <(git ls-tree -r HEAD --name-only | sort) || true)"

  local path excluded prefix
  while IFS= read -r path; do
    [ -z "$path" ] && continue
    excluded=false
    for prefix in "${EXCLUDE_PATHS[@]}"; do
      # Match the entry itself or anything beneath it.
      if [ "$path" = "$prefix" ] || [ "${path#"$prefix"/}" != "$path" ]; then
        excluded=true
        break
      fi
    done
    # Deliberately removed on the internal line: present in the mirror's tree but
    # deleted by an internal commit rather than never having existed.
    if [ "$excluded" = false ] && git log --oneline -1 --diff-filter=D -- "$path" | grep -q .; then
      excluded=true
    fi
    [ "$excluded" = false ] && orphans="${orphans}${path}"$'\n'
  done <<< "$candidates"

  orphans="$(printf '%s' "$orphans" | sed '/^$/d')"

  if [ -n "$orphans" ]; then
    echo "error: $GITHUB_REMOTE/main holds content absent from the internal line" >&2
    echo "$orphans" | sed 's/^/  /' >&2
    echo "hint: the public mirror accepts pull requests, so a force-push can destroy" >&2
    echo "      work that did not originate internally. Reconcile these paths onto" >&2
    echo "      the internal line first, or confirm they were deliberately removed." >&2
    return 1
  fi

  echo "ok: $GITHUB_REMOTE/main is behind, not divergent — safe to publish"
}

assert_no_divergence

# ---------------------------------------------------------------------------
# Filtered tree + notes-carrying retag, in a THROWAWAY WORKTREE
# ---------------------------------------------------------------------------

# The operator's clone is never mutated. github-push.sh's `git tag -f` ran in the
# invoking clone and is what corrupted local v0.1.7; a worktree gives the amend
# and retag their own index, HEAD, and checkout, so local tags are untouched by
# construction rather than by care.
WORKTREE_DIR="$(mktemp -d)/publish"
cleanup() {
  rm -f "$NOTES_FILE"
  if [ -n "${WORKTREE_DIR:-}" ] && [ -d "$WORKTREE_DIR" ]; then
    git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true
  fi
  git worktree prune 2>/dev/null || true
}
trap cleanup EXIT

git worktree add --quiet --detach "$WORKTREE_DIR" "refs/tags/$TAG"
cd "$WORKTREE_DIR"

git config user.email "ci@code.aws.dev"
git config user.name "GitLab CI"

# Snapshot tracking state BEFORE the removal loop. Afterwards every entry is
# absent, so "removed" and "never present" are indistinguishable.
TRACKED_BEFORE=()
for path in "${EXCLUDE_PATHS[@]}"; do
  if git ls-files --error-unmatch "$path" &>/dev/null; then
    TRACKED_BEFORE+=("$path")
  fi
done

was_tracked_before() {
  local needle="$1" entry
  for entry in "${TRACKED_BEFORE[@]+"${TRACKED_BEFORE[@]}"}"; do
    [ "$entry" = "$needle" ] && return 0
  done
  return 1
}

for path in "${EXCLUDE_PATHS[@]}"; do
  if git ls-files --error-unmatch "$path" &>/dev/null; then
    git rm -rq "$path"
  fi
done

# Defensively strip any generated artifacts that may have slipped into git.
# These match scripts/.gitignore: top-level scripts/*.mk except test.mk, and
# top-level scripts/*.md except INSTALL-RUNBOOK.md. infra/scripts/ is untouched.
if [ -d scripts ]; then
  while IFS= read -r -d '' path; do
    git ls-files --error-unmatch "$path" &>/dev/null && git rm -qf "$path"
  done < <(find scripts -maxdepth 1 -type f \( -name '*.mk' ! -name 'test.mk' \) -print0)

  while IFS= read -r -d '' path; do
    git ls-files --error-unmatch "$path" &>/dev/null && git rm -qf "$path"
  done < <(find scripts -maxdepth 1 -type f \( -name '*.md' ! -name 'INSTALL-RUNBOOK.md' \) -print0)
fi

git commit --quiet --amend --no-edit
AMENDED_COMMIT="$(git rev-parse HEAD)"

# Build the annotated tag object for the amended commit, carrying the notes.
#
# `git tag` is deliberately NOT used: a worktree shares refs/tags with the main
# repository, so `git tag -f` here would move the OPERATOR'S tag — the exact
# mechanism that corrupted local v0.1.7. Worktrees isolate the index, HEAD, and
# checkout; they do NOT isolate refs. `git mktag` writes the object into the
# object store and writes no ref at all, so nothing in the operator's clone
# changes and the object can still be pushed by SHA.
#
# THE CLEANUP MODE IS LOAD-BEARING. `git tag -a -m "$NOTES"` destroys every ##
# and ### heading via git's default --cleanup=strip, EXITS 0, and warns nobody —
# a release published that way carries a flat, ungrouped, unversioned bullet
# list. mktag is verbatim by construction: it stores the body byte-for-byte.
TAG_OBJECT="$(
  {
    echo "object $AMENDED_COMMIT"
    echo "type commit"
    echo "tag ${TAG#refs/tags/}"
    echo "tagger $(git config user.name) <$(git config user.email)> $(git log -1 --format=%ct HEAD) +0000"
    echo
    cat "$NOTES_FILE"
  } | git mktag
)"

# Assert rather than trust: the flattening failure mode is invisible otherwise.
if ! git cat-file tag "$TAG_OBJECT" | grep -q '^## \['; then
  echo "error: tag annotation lost its heading structure" >&2
  echo "hint: the notes body must be stored verbatim — git strips #-leading lines" >&2
  echo "      when a message goes through --cleanup=strip (the default for -m)" >&2
  exit 1
fi
echo "ok: tag annotation preserves its heading structure"

# ---------------------------------------------------------------------------
# Report or publish
# ---------------------------------------------------------------------------

if [ "$DRY_RUN" = true ]; then
  echo
  echo "--- filtered paths ---"
  for path in "${EXCLUDE_PATHS[@]}"; do
    if git ls-files --error-unmatch "$path" &>/dev/null 2>&1; then
      echo "FAIL: $path still present" >&2
      exit 1
    fi
    if was_tracked_before "$path"; then
      echo "OK: $path removed"
    elif is_intentionally_absent "$path"; then
      echo "OK: $path absent (declared intentionally absent)"
    else
      echo "FAIL: $path was never tracked in HEAD — nothing was removed" >&2
      echo "hint: this is indistinguishable from a typo. Fix the path, or add it" >&2
      echo "      to INTENTIONALLY_ABSENT with a reason if the absence is deliberate." >&2
      exit 1
    fi
  done
  echo "--- end filtered paths ---"
  echo
  echo "dry-run: nothing was pushed. To publish:"
  echo "  run the publish:github job with CONFIRM_TAG=$TAG"
else
  if [ "${CONFIRM_TAG:-}" != "$TAG" ]; then
    echo "error: publishing to the public mirror requires explicit confirmation" >&2
    echo "would publish: $TAG" >&2
    echo "hint: re-run with CONFIRM_TAG=$TAG" >&2
    exit 1
  fi

  if git fetch --quiet "$GITHUB_REMOTE" main 2>/dev/null; then
    git push --quiet "$GITHUB_REMOTE" "$AMENDED_COMMIT:refs/heads/main" --force-with-lease
  else
    echo "$GITHUB_REMOTE:main not fetchable (likely first release) — using --force"
    git push --quiet "$GITHUB_REMOTE" "$AMENDED_COMMIT:refs/heads/main" --force
  fi
  # Push the tag OBJECT by SHA. No local ref named $TAG was created or moved, so
  # the operator's clone is untouched.
  git push --quiet --force "$GITHUB_REMOTE" "$TAG_OBJECT:refs/tags/$TAG"

  echo "ok: published $TAG to $GITHUB_REMOTE (filtered ${#EXCLUDE_PATHS[@]} internal paths)"
  echo "    the GitHub Release is created by .github/workflows/release.yml from the tag annotation"
fi

cd "$REPO_ROOT"
