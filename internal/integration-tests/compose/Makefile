# The compose scenario — drives /ipa-init then /ipa-compose, and stops.
#
# Bare `make` prints help and creates nothing.

# Derived from MAKEFILE_LIST rather than from the caller's cwd, so `make -C compose`
# works from anywhere.
HERE := $(dir $(lastword $(MAKEFILE_LIST)))
ROOT := $(abspath $(HERE)..)

# VERBOSE trap, and it is worth restating because the obvious form is wrong:
#
#   WRONG: $(if $(VERBOSE),-vv -s,)
#
# Make's $(if) branches on NON-EMPTINESS, not truth. `VERBOSE=0` is non-empty, so that
# form turns verbosity ON when a user asked for it off. `filter-out` against a list of
# disabling words is what actually tests the value.
OFF := 0 no false off
VERBOSE ?= 1
PYTEST_FLAGS := $(if $(filter-out $(OFF),$(VERBOSE)),-vv -s -rs --log-cli-level=INFO,-q)

# `python -m pytest`, NOT bare `pytest`, and this is the load-bearing detail of the
# whole layout. Running from $(ROOT) is what makes `harness` importable — but only
# because `-m` places the working directory on sys.path. The bare `pytest` console
# script does NOT, and every test module then fails with
# `ModuleNotFoundError: No module named 'harness'`. Measured, not assumed.
#
# This is why no `[build-system]`, no editable install and no `pythonpath` entry are
# needed: the interpreter's working directory is the package's parent.
PYTEST ?= uv run python -m pytest

.DEFAULT_GOAL := help

.PHONY: help test test-ci clean

help:
	@echo ""
	@echo "compose scenario — /ipa-init then /ipa-compose. Stops before /ipa-prepare."
	@echo ""
	@echo "  make test      Drive the agent to /ipa-compose.       (MEASURED: ~\$$0.94, ~6m20s)"
	@echo "                 Creates ONE real {ns}-dev-security stack (2 IAM roles:"
	@echo "                 free, but real). No billable infrastructure."
	@echo ""
	@echo "  make test-ci   Same drive, but unmet prerequisites FAIL instead of"
	@echo "                 skipping, and results are written to junit-compose.xml."
	@echo ""
	@echo "  make clean     Remove this scenario's caches."
	@echo ""
	@echo "  Currently RED — /ipa-compose generates none of its eight artifacts."
	@echo "  See README.md and DECISIONS.md F3 before reading a failure as a regression."
	@echo ""
	@echo "  Remove what a run leaves standing, from the harness root:"
	@echo "    make teardown-namespace NAMESPACE=<ns>"
	@echo ""

# IPA_IT_MAX_BUDGET_USD is set INLINE on the recipe line, never as `export` and never as
# a file-level variable. The two scenarios' ceilings differ threefold, and an ambient
# value would apply to every recipe here and to anything else run on the same runner —
# so this scenario's $5 ceiling could cap a deploy run and stop it mid-deployment, which
# is indistinguishable from a wedge and leaves partial infrastructure standing.
test:
	cd "$(ROOT)" && IPA_IT_MAX_BUDGET_USD=5 $(PYTEST) $(PYTEST_FLAGS) \
		-c compose/pytest.ini compose/ -m integration

# IPA_IT_STRICT_PREFLIGHT=1 is inline here and on no other line. In CI an unmet
# prerequisite must FAIL rather than skip: a build that skips every billable test exits 0
# having tested nothing, which reads as a pass.
#
# --junitxml names THIS scenario's report, so two scenarios' results stay distinguishable
# and the pipeline's junit-*.xml glob collects whichever ran.
test-ci:
	cd "$(ROOT)" && IPA_IT_MAX_BUDGET_USD=5 IPA_IT_STRICT_PREFLIGHT=1 \
		$(PYTEST) $(PYTEST_FLAGS) -c compose/pytest.ini compose/ \
		-m integration --junitxml=junit-compose.xml

clean:
	rm -rf $(HERE).pytest_cache $(HERE)__pycache__
