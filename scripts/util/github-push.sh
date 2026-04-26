#!/usr/bin/env bash
# Filter internal-only paths from the release commit and push to GitHub.
# Invoked by the .gitlab-ci.yml github-release job.
# Usage: scripts/util/github-push.sh [--dry-run]
#
# To add a new internal-only path, append it to the EXCLUDE_PATHS array below.

set -euo pipefail

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

GITHUB_REMOTE="github"
GITHUB_REPO="git@github.com:aws-samples/sample-innovation-patterns.git"
TAG="${CI_COMMIT_TAG:-$(git describe --tags --exact-match 2>/dev/null || echo '')}"

if [ -z "$TAG" ]; then
  echo "error: no tag on current commit" >&2
  exit 1
fi

# Paths that stay in GitLab but must never ship to GitHub.
EXCLUDE_PATHS=(
  ".gitlab-ci.yml"
  ".gitlab"
  ".specify"
  "docs/docs/guides/releasing.md"
)

git remote add "$GITHUB_REMOTE" "$GITHUB_REPO" 2>/dev/null || true

TEMP_BRANCH="github-release-$(date +%s)"
git checkout -b "$TEMP_BRANCH"

for path in "${EXCLUDE_PATHS[@]}"; do
  if git ls-files --error-unmatch "$path" &>/dev/null; then
    git rm -rf "$path"
  fi
done

git commit --amend --no-edit

# The amend changed the commit SHA; move the tag to match so the GitHub tag/main
# agree and the auto-generated release tarball contains the filtered tree.
# This retag is local only — never pushed back to GitLab origin.
git tag -f "$TAG"

if [ "$DRY_RUN" = true ]; then
  echo "dry-run: would push $TEMP_BRANCH as main and tag $TAG to $GITHUB_REMOTE"
  for path in "${EXCLUDE_PATHS[@]}"; do
    if git ls-files --error-unmatch "$path" &>/dev/null 2>&1; then
      echo "FAIL: $path still present" >&2
      exit 1
    fi
    echo "OK: $path removed"
  done
else
  if git fetch "$GITHUB_REMOTE" main 2>/dev/null; then
    git push "$GITHUB_REMOTE" "$TEMP_BRANCH:main" --force-with-lease
  else
    echo "github:main not fetchable (likely first release) — using --force"
    git push "$GITHUB_REMOTE" "$TEMP_BRANCH:main" --force
  fi
  git push "$GITHUB_REMOTE" "$TAG"
fi

git checkout -
git branch -D "$TEMP_BRANCH"

echo "ok: pushed to GitHub (filtered ${#EXCLUDE_PATHS[@]} internal paths)"
