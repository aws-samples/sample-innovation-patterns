#!/usr/bin/env bash
# DEPRECATED entry point. Delegates to internal/release/publish-github.sh.
#
# This script used to be the whole GitHub publish path. It has been superseded
# because it could not express what selective publishing needs, and because two of
# its behaviors were hazards:
#
#   - It ran `git tag -f` in the INVOKING clone, which is what corrupted the
#     local v0.1.7 tag. The replacement builds the tag object without writing any
#     local ref, so the operator's tags are never moved.
#   - It relied on --force-with-lease to protect the public mirror. The lease
#     passes precisely when a fresh clone is used (which is always, in CI), so it
#     never guarded against a public contribution being clobbered. The replacement
#     asserts on content explicitly, and unshallows first so the assertion reasons
#     from a complete graph.
#
# It also carried no release notes: notes now travel on the annotated tag, which
# is how a published Release can cover several skipped versions.
#
# Kept as a wrapper rather than deleted so existing references and muscle memory
# keep working, while exactly ONE implementation of the filtered push exists.
#
# Usage: infra/scripts/github-push.sh [--dry-run]   (see the new script for TAG=)

set -euo pipefail

echo "note: github-push.sh is deprecated — delegating to internal/release/publish-github.sh" >&2

REPO_ROOT="$(git rev-parse --show-toplevel)"
exec bash "$REPO_ROOT/internal/release/publish-github.sh" "$@"
