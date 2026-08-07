#!/usr/bin/env bash
# Create a GitLab Release object for an existing tag.
# Usage: infra/scripts/gitlab-release.sh <tag> <notes-file>
#
# Why the API rather than the `release:` CI keyword: that keyword is implemented
# by `release-cli`, a Go binary that must be present in the job image. The
# release jobs run on python:3.12-bookworm because they need git-cliff, and
# release-cli is not in it. The REST API needs no extra tooling and no extra
# credential — CI_JOB_TOKEN is issued to every job automatically.
#
# A tag alone is not a release. Before this, internal releases were bare
# (properly annotated) tags with no Release object.

set -euo pipefail

TAG="${1:?usage: gitlab-release.sh <tag> <notes-file>}"
NOTES_FILE="${2:?usage: gitlab-release.sh <tag> <notes-file>}"

if [ ! -f "$NOTES_FILE" ]; then
  echo "error: notes file not found: $NOTES_FILE" >&2
  exit 1
fi

: "${CI_API_V4_URL:?CI_API_V4_URL is unset — this script runs inside GitLab CI}"
: "${CI_PROJECT_ID:?CI_PROJECT_ID is unset — this script runs inside GitLab CI}"
: "${CI_JOB_TOKEN:?CI_JOB_TOKEN is unset — this script runs inside GitLab CI}"

# Build the JSON body with python rather than string interpolation: the notes
# contain newlines, backticks, quotes, and asterisks, all of which need escaping.
PAYLOAD=$(TAG="$TAG" NOTES_FILE="$NOTES_FILE" python3 -c '
import json, os
with open(os.environ["NOTES_FILE"], encoding="utf-8") as fh:
    description = fh.read()
print(json.dumps({"name": os.environ["TAG"], "tag_name": os.environ["TAG"], "description": description}))
')

HTTP_CODE=$(printf '%s' "$PAYLOAD" | curl --silent --show-error \
  --output /tmp/gitlab-release-response.json \
  --write-out '%{http_code}' \
  --request POST \
  --header "JOB-TOKEN: $CI_JOB_TOKEN" \
  --header "Content-Type: application/json" \
  --data-binary @- \
  "$CI_API_V4_URL/projects/$CI_PROJECT_ID/releases")

if [ "$HTTP_CODE" = "201" ]; then
  echo "ok: created GitLab Release $TAG"
elif [ "$HTTP_CODE" = "409" ]; then
  # Idempotent: a Release for this tag already exists. Not a failure — the tag
  # is pushed and the Release is present, which is the desired end state.
  echo "ok: GitLab Release $TAG already exists"
else
  echo "error: failed to create GitLab Release $TAG (HTTP $HTTP_CODE)" >&2
  cat /tmp/gitlab-release-response.json >&2
  echo >&2
  echo "hint: the tag was pushed successfully — only the Release object failed." >&2
  echo "      Re-running this script is safe; it is idempotent." >&2
  exit 1
fi
