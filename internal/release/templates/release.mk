# Release automation — forge-agnostic reference implementation.
#
# Works with `make`, `git`, and `git-cliff` alone. No CI system, no forge, and no
# framework required. Any forge-specific step is SKIPPED rather than failed when
# the forge is absent, so this works in a repository with no remote at all.
#
# Usage:
#   make -f release.mk release-preview     # what would be released; creates nothing
#   make -f release.mk release             # changelog + annotated tag
#   make -f release.mk release VERSION=1.2.3   # explicit override
#
# Requires: git-cliff (https://git-cliff.org) — `brew install git-cliff`

.PHONY: release release-preview release-changelog release-tag release-forge

# The version is DERIVED from Conventional Commit history, not stored in a file.
# A version file conflates two different questions — "what is next?" (a
# release-time derivation) and "what is current?" (a build-time display) — and
# being hand-maintained, it drifts from the tags that actually define releases.
VERSION ?= $(shell git-cliff --bumped-version 2>/dev/null | sed 's/^v//')
TAG = v$(VERSION)
LATEST_TAG = $(shell git describe --tags --abbrev=0 2>/dev/null)

# Where the notes body is staged. Kept in a file rather than a shell variable:
# the content is multi-line and contains backticks and asterisks that shell
# quoting mangles.
NOTES_FILE ?= .release-notes.md

define require_releasable
	@command -v git-cliff >/dev/null 2>&1 || { \
	  echo "error: git-cliff is not installed" >&2; \
	  echo "hint: brew install git-cliff  (or see https://git-cliff.org)" >&2; \
	  exit 1; \
	}
	@if [ -z "$(VERSION)" ]; then \
	  echo "error: could not derive a version from commit history" >&2; \
	  echo "hint: are there any commits? Is cliff.toml present?" >&2; \
	  exit 1; \
	fi
	@if [ "$(TAG)" = "$(LATEST_TAG)" ]; then \
	  echo "Nothing to release — derived version equals the current tag ($(LATEST_TAG))."; \
	  echo "Only conventional commits (feat:, fix:, ...) derive a new version."; \
	  exit 1; \
	fi
endef

# Print what a release would do. Creates nothing, so it is safe to run always.
release-preview:
	@echo "current release: $(if $(LATEST_TAG),$(LATEST_TAG),none)"
	@echo "would release:   $(TAG)"
	@if [ "$(TAG)" = "$(LATEST_TAG)" ]; then \
	  echo ""; \
	  echo "Nothing to release — no commits since $(LATEST_TAG) affect the version."; \
	else \
	  echo ""; \
	  echo "--- release notes for $(TAG) ---"; \
	  git-cliff --unreleased --strip all; \
	  echo "--- end release notes ---"; \
	fi

# Regenerate the committed changelog through the derived version.
release-changelog:
	$(call require_releasable)
	@git-cliff --tag "$(TAG)" -o CHANGELOG.md
	@echo "ok: wrote CHANGELOG.md through $(TAG)"

# Create the annotated tag, carrying the release notes on the annotation.
release-tag:
	$(call require_releasable)
#	--tag stamps the heading as "## [X.Y.Z] - <date>". Without it the notes are
#	headed "## [Unreleased]", which is wrong on a tag that names a version.
	@git-cliff --unreleased --tag "$(TAG)" --strip all > $(NOTES_FILE)
	@if [ ! -s $(NOTES_FILE) ]; then \
	  echo "error: generated notes are empty" >&2; rm -f $(NOTES_FILE); exit 1; \
	fi
#	--cleanup=verbatim is LOAD-BEARING. Without it, git's default --cleanup=strip
#	treats every #-leading line as a comment and silently deletes all Markdown
#	headings from the annotation. It exits 0 and warns nobody.
	@git tag -a "$(TAG)" --cleanup=verbatim -F $(NOTES_FILE)
#	Assert rather than trust: the failure above is otherwise invisible.
	@git tag -l --format='%(contents)' "$(TAG)" | grep -q '^## \[' || { \
	  echo "error: tag annotation lost its heading structure" >&2; \
	  echo "hint: --cleanup=verbatim is required" >&2; \
	  git tag -d "$(TAG)" >/dev/null; rm -f $(NOTES_FILE); exit 1; \
	}
	@rm -f $(NOTES_FILE)
	@echo "ok: created annotated tag $(TAG)"

# Push the tag and create a forge Release, IF a forge is configured.
#
# SKIPPED, not failed, when absent: a solution may have no forge of any kind, and
# a release target that fails in that case is unusable rather than merely limited.
release-forge:
	@if ! git remote get-url origin >/dev/null 2>&1; then \
	  echo "skip: no 'origin' remote configured — tag created locally only"; \
	  echo "      (push it yourself when a remote exists: git push <remote> $(TAG))"; \
	elif [ -n "$(NO_PUSH)" ]; then \
	  echo "skip: NO_PUSH set — tag created locally only"; \
	else \
	  git push origin "$(TAG)" && echo "ok: pushed $(TAG) to origin"; \
	  if command -v gh >/dev/null 2>&1 && gh repo view >/dev/null 2>&1; then \
	    gh release create "$(TAG)" --notes "$$(git tag -l --format='%(contents)' $(TAG))" \
	      && echo "ok: created GitHub Release $(TAG)"; \
	  elif command -v glab >/dev/null 2>&1 && glab repo view >/dev/null 2>&1; then \
	    glab release create "$(TAG)" --notes "$$(git tag -l --format='%(contents)' $(TAG))" \
	      && echo "ok: created GitLab Release $(TAG)"; \
	  else \
	    echo "skip: no forge CLI available (gh/glab) — tag pushed, no Release object"; \
	    echo "      the annotated tag carries the notes, so a Release can be made later"; \
	  fi; \
	fi

# The whole flow. Changelog and tag always; forge steps only if a forge exists.
release: release-changelog release-tag release-forge
	@echo ""
	@echo "Released $(TAG)."
	@echo "The CHANGELOG.md change is uncommitted — review and commit it."
