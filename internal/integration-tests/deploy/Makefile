# The deploy scenario — the FULL lifecycle. BILLABLE.
#
# Bare `make` prints help and creates nothing.

# Derived from MAKEFILE_LIST rather than from the caller's cwd, so `make -C deploy`
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
#
# Verbose is the DEFAULT on purpose here especially. This run measured 32 minutes
# (2026-08-19), and per-test output is the only way to distinguish progress from a wedge —
# a wedged half-hour billable run with nothing on screen is not recoverable by re-running
# it.
OFF := 0 no false off
VERBOSE ?= 1
PYTEST_FLAGS := $(if $(filter-out $(OFF),$(VERBOSE)),-vv -s -rs --log-cli-level=INFO,-q)

# `python -m pytest`, NOT bare `pytest`. Running from $(ROOT) is what makes `harness`
# importable — but only because `-m` places the working directory on sys.path. The bare
# `pytest` console script does NOT, and every test module then fails with
# `ModuleNotFoundError: No module named 'harness'`. Measured, not assumed.
PYTEST ?= uv run python -m pytest

.DEFAULT_GOAL := help

.PHONY: help test test-teardown test-ci clean

help:
	@echo ""
	@echo "deploy scenario — FULL lifecycle: /ipa-init, /ipa-compose, /ipa-prepare, /ipa-deploy."
	@echo ""
	@echo "  make test           Deploy SEVEN stacks and LEAVE THEM STANDING, so you can"
	@echo "                      open the app in a browser and confirm by eye what the"
	@echo "                      assertions claim. CloudFront + ECR + 2 Lambdas + SQS +"
	@echo "                      DynamoDB + S3.               (BILLABLE — cost UNMEASURED)"
	@echo ""
	@echo "  make test-teardown  Verify-then-remove this run's stacks. Needs BOTH the"
	@echo "                      'teardown' marker and IPA_IT_TEARDOWN=1."
	@echo ""
	@echo "  make test-ci        Deploy THEN tear down, in ONE pytest run, with unmet"
	@echo "                      prerequisites failing instead of skipping."
	@echo "                                                   (BILLABLE, then frees it)"
	@echo ""
	@echo "  make clean          Remove this scenario's caches."
	@echo ""
	@echo "  Cost is UNMEASURED, not estimated — this run has never completed. No figure"
	@echo "  is given rather than a predicted one. See README.md."
	@echo ""
	@echo "  Both prior runs stopped at COMPOSITION — /ipa-compose generated none of its"
	@echo "  eight artifacts (DECISIONS.md F3, F8). Fixed in the skills; NOT re-run since,"
	@echo "  so the deployment assertions remain unexercised. A truncated lifecycle now"
	@echo "  fails ONCE, in deploy_run, naming what is missing."
	@echo ""
	@echo "  Remove what a run leaves standing, from the harness root:"
	@echo "    make teardown-namespace NAMESPACE=<ns>"
	@echo ""

# IPA_IT_FULL_MAX_BUDGET_USD is set INLINE, never as `export` and never as a file-level
# variable. This scenario's ceiling is 3x the compose scenario's; an ambient value would
# apply to every recipe here and to anything else on the same runner.
#
# NOTE: no teardown opt-in on this line. `test` LEAVES THE STACKS STANDING, deliberately
# — that is what lets a maintainer confirm by eye what the assertions claim.
test:
	cd "$(ROOT)" && IPA_IT_FULL_MAX_BUDGET_USD=$${IPA_IT_FULL_MAX_BUDGET_USD:-15} \
		$(PYTEST) $(PYTEST_FLAGS) -c deploy/pytest.ini deploy/ -m integration

# Both teardown opt-ins are set INLINE on this recipe line — never as `export`, never as
# a file-level variable, never as a pipeline variable. An ambient variable applies to
# every phase of every build, which is precisely the "persists invisibly" case the
# two-part opt-in exists to prevent — and declaring it ambiently defeats the mechanism
# SILENTLY, because the invocation that needs it still works and the failure only appears
# the day someone runs another target on the same runner.
test-teardown:
	cd "$(ROOT)" && IPA_IT_TEARDOWN=1 \
		$(PYTEST) $(PYTEST_FLAGS) -c deploy/pytest.ini deploy/ -m teardown

# ONE pytest invocation with the teardown marker NOT deselected, so deploy and teardown
# share a namespace as a property of the session fixture rather than of a hand-off.
#
# TWO invocations would generate two namespaces, and the second would tear down a
# namespace that never existed — which finds nothing, removes nothing, and PASSES,
# leaving the deployment standing and billing while reporting that it was removed.
#
# IPA_IT_STRICT_PREFLIGHT=1 because in CI an unmet prerequisite must FAIL rather than
# skip: a build that skips every billable test exits 0 having tested nothing.
test-ci:
	cd "$(ROOT)" && IPA_IT_STRICT_PREFLIGHT=1 IPA_IT_TEARDOWN=1 \
		IPA_IT_FULL_MAX_BUDGET_USD=$${IPA_IT_FULL_MAX_BUDGET_USD:-15} \
		$(PYTEST) $(PYTEST_FLAGS) -c deploy/pytest.ini deploy/ \
		-m "integration or teardown" --junitxml=junit-deploy.xml

clean:
	rm -rf $(HERE).pytest_cache $(HERE)__pycache__
