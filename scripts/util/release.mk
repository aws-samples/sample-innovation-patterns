# Release automation targets
# Usage: make -f scripts/util/release.mk <target>

-include .env

.PHONY: release-check release-prep

# Verify VERSION file matches current git tag
release-check:
	@bash scripts/util/release-check.sh

# Prepare a release: stamp VERSION and create CHANGELOG skeleton
# Usage: make -f scripts/util/release.mk release-prep VERSION=0.2.0
release-prep:
ifndef VERSION
	$(error VERSION is required. Usage: make -f scripts/util/release.mk release-prep VERSION=0.2.0)
endif
	@echo "$(VERSION)" > VERSION
	@echo "Stamped VERSION=$(VERSION)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Update CHANGELOG.md with release notes under [$(VERSION)]"
	@echo "  2. Commit: git commit -am 'Release v$(VERSION)'"
	@echo "  3. Create MR to main"
