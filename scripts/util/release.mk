# Release automation targets
# Usage: make -f scripts/util/release.mk <target>

-include .env

.PHONY: release-check release-prep release-changelog

# Verify VERSION file matches current git tag
release-check:
	@bash scripts/util/release-check.sh

# Generate CHANGELOG.md from conventional commit history using git-cliff
# Requires: git-cliff (install: cargo install git-cliff, or brew install git-cliff)
release-changelog:
ifndef VERSION
	$(error VERSION is required. Usage: make -f scripts/util/release.mk release-changelog VERSION=0.2.0)
endif
	@git-cliff --tag "v$(VERSION)" -o CHANGELOG.md
	@echo "Generated CHANGELOG.md through v$(VERSION)"

# Prepare a release: stamp VERSION, generate CHANGELOG, print next steps
# Usage: make -f scripts/util/release.mk release-prep VERSION=0.2.0
release-prep:
ifndef VERSION
	$(error VERSION is required. Usage: make -f scripts/util/release.mk release-prep VERSION=0.2.0)
endif
	@echo "$(VERSION)" > VERSION
	@echo "Stamped VERSION=$(VERSION)"
	@$(MAKE) -f scripts/util/release.mk release-changelog VERSION=$(VERSION)
	@echo ""
	@echo "Next steps:"
	@echo "  1. Review and edit CHANGELOG.md (git-cliff output is a starting point)"
	@echo "  2. Commit: git commit -am 'chore: release v$(VERSION)'"
	@echo "  3. Push to main"
	@echo "  4. Click 'Tag & Release' in the GitLab pipeline"
