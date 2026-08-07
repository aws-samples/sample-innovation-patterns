# Release automation targets
# Usage: make -f infra/scripts/release.mk <target>

-include .env

.PHONY: release-check release-prep release-changelog release-preview

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
# Creates nothing — the local counterpart of the release:preview CI job.
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

# Generate CHANGELOG.md from conventional commit history using git-cliff
# Requires: git-cliff (install: cargo install git-cliff, or brew install git-cliff)
release-changelog:
	$(call check_releasable)
	@git-cliff --tag "v$(VERSION)" -o CHANGELOG.md
	@echo "Generated CHANGELOG.md through v$(VERSION)"

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
	@echo "Next steps:"
	@echo "  1. Review and edit CHANGELOG.md (git-cliff output is a starting point)"
	@echo "  2. Commit: git commit -am 'chore: release v$(VERSION)'"
	@echo "  3. Push to main"
	@echo "  4. Run the 'release' job in the GitLab pipeline for that commit"
	@echo "     (it derives the tag itself — no version needs to be typed)"
