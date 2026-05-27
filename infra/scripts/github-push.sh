#!/usr/bin/env bash
# Filter internal-only paths from the release commit and push to GitHub.
# Invoked by the .gitlab-ci.yml github-release job.
# Usage: infra/scripts/github-push.sh [--dry-run]
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
  "docs/docs/developer-docs/internal"
  "docs/docs/guides/releasing.md"
  "scripts/.gitignore"
)

git remote add "$GITHUB_REMOTE" "$GITHUB_REPO" 2>/dev/null || true

# Ensure git has a committer identity for the amend below.
# Only set locally if not already configured (e.g., by a previous auto-tag step).
git config user.email >/dev/null 2>&1 || git config user.email "ci@code.aws.dev"
git config user.name  >/dev/null 2>&1 || git config user.name  "GitLab CI"

TEMP_BRANCH="github-release-$(date +%s)"
git checkout -b "$TEMP_BRANCH"

for path in "${EXCLUDE_PATHS[@]}"; do
  if git ls-files --error-unmatch "$path" &>/dev/null; then
    git rm -rf "$path"
  fi
done

# Defensively strip any generated artifacts that may have slipped into git.
# These match scripts/.gitignore: top-level scripts/*.mk except test.mk, and
# top-level scripts/*.md except INSTALL-RUNBOOK.md. infra/scripts/ is untouched.
while IFS= read -r -d '' path; do
  if git ls-files --error-unmatch "$path" &>/dev/null; then
    git rm -f "$path"
  fi
done < <(find scripts -maxdepth 1 -type f \( -name '*.mk' ! -name 'test.mk' \) -print0)

while IFS= read -r -d '' path; do
  if git ls-files --error-unmatch "$path" &>/dev/null; then
    git rm -f "$path"
  fi
done < <(find scripts -maxdepth 1 -type f \( -name '*.md' ! -name 'INSTALL-RUNBOOK.md' \) -print0)

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
