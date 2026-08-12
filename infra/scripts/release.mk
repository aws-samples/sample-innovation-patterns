# Release automation targets
# Usage: make -f infra/scripts/release.mk <target>

-include .env

.PHONY: release-check release-prep release-changelog release-preview release-prepare

# The version is DERIVED from tags and Conventional Commit history. There is no
# VERSION file — it was retired because it conflated two different questions
# ("what is next?" and "what is current?") and was hand-maintained, so it was
# routinely wrong. Override explicitly when you need to: VERSION=0.3.0
VERSION ?= $(shell git-cliff --bumped-version 2>/dev/null | sed 's/^v//')
LATEST_TAG = $(shell git describe --tags --abbrev=0 2>/dev/null)

# Guard: refuse to act when the derived version equals the newest tag, which
# means nothing in the window affects the version.
define check_releasable
	@if [ -z "$(VERSION)" ]; then \
	  echo "error: could not derive a version" >&2; \
	  echo "hint: is git-cliff installed? (brew install git-cliff)" >&2; \
	  exit 1; \
	fi
	@if [ "v$(VERSION)" = "$(LATEST_TAG)" ]; then \
	  echo "Nothing to release — derived version equals the current tag ($(LATEST_TAG))."; \
	  echo "Only conventional commits (feat:, fix:, ...) derive a new version."; \
	  exit 1; \
	fi
endef

# Verify tag hygiene and that the tag under release matches the derived version
release-check:
	@bash infra/scripts/release-check.sh

# Print the version that would be cut and the notes that would be published.
# Creates nothing. This is the ONLY preview — there is no CI preview job, because
# this target and release:prepare (whose MR diff IS the notes) both already answer
# the question it would have answered.
release-preview:
	@echo "current release: $(if $(LATEST_TAG),$(LATEST_TAG),none)"
	@echo "would release:   v$(VERSION)"
	@if [ "v$(VERSION)" = "$(LATEST_TAG)" ]; then \
	  echo ""; \
	  echo "Nothing to release — no commits since $(LATEST_TAG) affect the version."; \
	else \
	  echo ""; \
	  echo "--- release notes for v$(VERSION) ---"; \
	  git-cliff --unreleased --strip all; \
	  echo "--- end release notes ---"; \
	fi

# Regenerate CHANGELOG.md from conventional commit history using git-cliff.
# Requires: git-cliff (install: cargo install git-cliff, or brew install git-cliff)
#
# CHANGELOG.md is a GENERATED ARTIFACT — this rewrites the whole file, and any
# hand-edit is lost on the next release. Prose belongs in the COMMIT BODY, which
# cliff.toml renders as indented continuation text under each bullet.
#
# CHANGELOG_FLOOR is the cutover: everything after it is generated, everything at
# or before it is frozen in cliff.toml's `footer`. See infra/scripts/changelog-lib.sh
# for the full rationale — the value is defined there so that this makefile, the
# release-check assertion, and release-prepare.sh cannot disagree about it.
#
# Read from the fragment, with the literal default as a fallback so this makefile
# still works if invoked from a checkout where the fragment is absent.
CHANGELOG_LIB = infra/scripts/changelog-lib.sh
CHANGELOG_FLOOR ?= $(shell sed -n 's/^CHANGELOG_FLOOR="\$${CHANGELOG_FLOOR:-\(v[0-9.]*\)}"/\1/p' $(CHANGELOG_LIB) 2>/dev/null || true)
CHANGELOG_FLOOR := $(if $(CHANGELOG_FLOOR),$(CHANGELOG_FLOOR),v0.1.4)

release-changelog:
	$(call check_releasable)
	@git-cliff "refs/tags/$(CHANGELOG_FLOOR).." --tag "v$(VERSION)" -o CHANGELOG.md
	@echo "Regenerated CHANGELOG.md through v$(VERSION) (floor: $(CHANGELOG_FLOOR))"

# Prepare a release: generate CHANGELOG, print next steps.
# Confirms the derived version before writing anything — the version is derived
# rather than supplied, so the operator should see it before it is committed to.
release-prep:
	$(call check_releasable)
	@echo "Derived version: v$(VERSION) (current: $(if $(LATEST_TAG),$(LATEST_TAG),none))"
	@echo ""
	@printf 'Generate CHANGELOG.md for v%s? [y/N] ' "$(VERSION)"
	@read -r reply; case "$$reply" in [yY]*) ;; *) echo "Aborted."; exit 1 ;; esac
	@$(MAKE) -f infra/scripts/release.mk release-changelog VERSION=$(VERSION)
	@echo ""
	@echo "CHANGELOG.md is regenerated in your working tree, uncommitted."
	@echo ""
	@echo "This target is for INSPECTING the generated notes. It is not the release"
	@echo "flow — do not commit this and push it to main."
	@echo ""
	@echo "To actually prepare the release, discard this and run release-prepare,"
	@echo "which puts the same content on a release branch behind a merge request:"
	@echo "  git checkout -- CHANGELOG.md"
	@echo "  make -f infra/scripts/release.mk release-prepare"
	@echo ""
	@echo "Or click 'release:prepare' in the GitLab pipeline for the current commit."

# Prepare a release for REVIEW: cut release/vX.Y.Z carrying a regenerated
# CHANGELOG.md and open a merge request. Creates NO tag.
#
# The local counterpart of the release:prepare CI job — same script, so the
# behaviour cannot differ between the two.
release-prepare:
	@bash infra/scripts/release-prepare.sh $(BUMP_MODE)
