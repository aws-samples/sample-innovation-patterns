#!/usr/bin/env bash
set -euo pipefail

version=$(tr -d '[:space:]' < VERSION)
tag="${CI_COMMIT_TAG:-$(git describe --tags --exact-match 2>/dev/null || echo '')}"

if [ -z "$tag" ]; then
  echo "error: no tag on current commit" >&2
  exit 1
fi

if [ "v$version" != "$tag" ]; then
  echo "error: VERSION file ($version) does not match tag ($tag)" >&2
  echo "hint: update VERSION to match, or retag the commit" >&2
  exit 1
fi

echo "ok: VERSION=$version matches tag=$tag"
