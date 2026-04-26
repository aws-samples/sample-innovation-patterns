#!/usr/bin/env bash
# Create a tar.gz archive of the repo, excluding .git, node_modules, .env,
# .venv, and anything matched by .gitignore.
#
# Usage: scripts/util/archive.sh [output-path]
#   Defaults to <repo-name>-<YYYYMMDD-HHMMSS>.tar.gz in the repo root.

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

repo_name="$(basename "$repo_root")"
timestamp="$(date +%Y%m%d-%H%M%S)"
output="${1:-${repo_name}-${timestamp}.tar.gz}"

# git ls-files honors .gitignore and the global excludes file:
#   -c  cached (tracked) files
#   -o  other (untracked) files
#   --exclude-standard  applies .gitignore, .git/info/exclude, and core.excludesFile
# This already skips .git/, .env, .venv/, node_modules (when gitignored), etc.
# We add belt-and-suspenders --exclude flags for node_modules / .env / .venv
# in case a working tree has them staged or missing from .gitignore.
git ls-files -co --exclude-standard -z \
  | tar --null -T - \
      --exclude='.git' \
      --exclude='node_modules' \
      --exclude='.env' \
      --exclude='.venv' \
      -czf "$output"

echo "Created archive: $output"
