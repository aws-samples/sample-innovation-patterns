# Release automation targets
# Usage: make -f infra/scripts/release.mk <target>
#
# Both targets DELEGATE to infra/scripts/release.sh rather than reimplementing
# it. That is not merely brevity: the previous release-preview derived the
# version itself and generated notes WITHOUT --tag, so it printed
# "## [Unreleased]" where a release prints "## [X.Y.Z] - <date>". Delegating
# makes that drift unreachable instead of merely corrected, and it is why no
# VERSION, LATEST_TAG, or releasable-guard definitions remain here — every one of
# them was a second copy of logic that now lives in one place.
#
# The version is DERIVED from tags and Conventional Commit history. There is no
# VERSION file and no way to request a version, so there is nothing to override.

-include .env

.PHONY: release-preview release

# Print the version that would be cut and the notes that would be published.
# Creates nothing, and needs no network. The local counterpart of the
# gitlab:release:preview CI job — same script, so they cannot disagree.
release-preview:
	@PREVIEW=1 bash infra/scripts/release.sh

# CUT THE RELEASE, FOR REAL, FROM THIS WORKSTATION. Tags origin, pushes the tag,
# and creates the GitLab Release object.
#
# Kept deliberately: the repo's idiom is that every script runs locally too, and
# this is the recovery path when CI is unavailable — a release process that can
# only run in CI blocks on its own infrastructure. It runs the same assertions
# the CI job does, and the tag-hygiene assertion actually earns its lines here,
# where a stale local tag silently derives from the wrong base.
#
# Creating the GitLab Release object needs CI_API_V4_URL, CI_PROJECT_ID, and
# CI_JOB_TOKEN. Outside CI the tag is still created and pushed, and that last
# step fails — re-run infra/scripts/gitlab-release.sh from a job, or create the
# Release in the web UI.
release:
	@bash infra/scripts/release.sh
