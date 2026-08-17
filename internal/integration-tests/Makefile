# IPA integration tests — maintainer-only harness.
#
# Bare `make` prints help and creates nothing.

# VERBOSE trap, and it is worth stating because the obvious form is wrong:
#
#   WRONG: $(if $(VERBOSE),-vv -s,)
#
# Make's $(if) branches on NON-EMPTINESS, not truth. `VERBOSE=0` is non-empty, so
# that form turns verbosity ON when a user asked for it off. `filter-out` against a
# list of disabling words is what actually tests the value.
OFF := 0 no false off
VERBOSE ?= 1
PYTEST_FLAGS := $(if $(filter-out $(OFF),$(VERBOSE)),-vv -s -rs --log-cli-level=INFO,-q)

# Verbose is the DEFAULT on purpose. On a run whose wall clock is deliberately
# unmeasured, per-test output is the only way to distinguish progress from a wedge —
# and a wedged twenty-minute billable run with nothing on screen is not recoverable
# by re-running it.

PYTHON      := uv run python
PYTEST      := uv run pytest
NAMESPACE   ?=
IPA_IT_REGION ?= us-east-1
export IPA_IT_REGION

.DEFAULT_GOAL := help

.PHONY: help preflight test-offline test-compose test test-teardown test-ci \
        list-stacks teardown-namespace clean

help:
	@echo ""
	@echo "IPA integration tests — maintainer-only. Nothing here runs in CI."
	@echo ""
	@echo "  FREE"
	@echo "    make test-offline        Offline suite, no AWS credentials needed  (~1s, \$$0)"
	@echo "    make list-stacks         List standing integration-test stacks     (\$$0, read-only)"
	@echo ""
	@echo "  COSTS MONEY — read internal/integration-tests/README.md first"
	@echo "    make preflight           Nine probes + Cognito check. Deploys and DELETES"
	@echo "                             two stacks under namespace 'itprobe'.    (cents)"
	@echo "    make test-compose        Drives the agent to /ipa-compose only. Model spend,"
	@echo "                             plus a REAL {ns}-{env}-security stack (2 free IAM"
	@echo "                             roles).                                   (model spend)"
	@echo "    make test                FULL LIFECYCLE. Deploys SEVEN stacks and LEAVES THEM"
	@echo "                             STANDING so you can open the app in a browser."
	@echo "                             CloudFront + ECR + 2 Lambdas + SQS + DynamoDB + S3."
	@echo "                             (BILLABLE — see README.md for the measured cost)"
	@echo ""
	@echo "  REMOVES BILLABLE RESOURCES"
	@echo "    make test-teardown       Verify-then-remove this run's stacks. Needs BOTH"
	@echo "                             the 'teardown' marker and IPA_IT_TEARDOWN=1."
	@echo "    make teardown-namespace NAMESPACE=<ns>"
	@echo "                             Remove ONE run's stacks. NAMESPACE is required;"
	@echo "                             empty is never treated as 'every run'."
	@echo ""
	@echo "  CI SEAM — nothing invokes it"
	@echo "    make test-ci             Full lifecycle THEN teardown, in one pytest run,"
	@echo "                             with unmet prerequisites failing instead of"
	@echo "                             skipping. Both teardown opt-ins are set inline on"
	@echo "                             that one recipe line. (BILLABLE, then frees it)"
	@echo ""
	@echo "  Options"
	@echo "    VERBOSE=0                Compact output (default is -vv -s)"
	@echo "    IPA_IT_NAMESPACE=<ns>    Pin the run namespace (validated at source)"
	@echo "    IPA_IT_STRICT_PREFLIGHT=1  Unmet prerequisites FAIL instead of skipping"
	@echo ""

preflight:
	$(PYTHON) -m preflight

test-offline:
	$(PYTEST) $(PYTEST_FLAGS) -m "not integration and not teardown"

test-compose:
	$(PYTEST) $(PYTEST_FLAGS) -m integration test_compose.py

test:
	$(PYTEST) $(PYTEST_FLAGS) -m integration

test-teardown:
	IPA_IT_TEARDOWN=1 $(PYTEST) $(PYTEST_FLAGS) -m teardown

# CI seam. NOTHING INVOKES THIS. Wiring it would commit the project to paying for a
# billable run on some trigger, which is a decision beyond this feature's scope.
#
# Both teardown opt-ins are set INLINE on this recipe line — never as `export`, never
# as a file-level variable, never as a pipeline variable. An ambient variable applies
# to every phase of every build, which is precisely the "persists invisibly" case the
# two-part opt-in exists to prevent — and declaring it ambiently defeats the mechanism
# SILENTLY, because the invocation that needs it still works and the failure only
# appears the day someone runs another target on the same runner.
#
# ONE pytest invocation with the teardown marker NOT deselected, so deploy and teardown
# share a namespace as a property of the session fixture rather than of a hand-off. Two
# invocations would need the namespace passed out of the first and into the second, and
# the failure mode is a teardown scoped to a namespace that never existed — which finds
# nothing, removes nothing, and PASSES, leaving the deployment standing while reporting
# that it was removed.
test-ci:
	IPA_IT_STRICT_PREFLIGHT=1 IPA_IT_TEARDOWN=1 $(PYTEST) $(PYTEST_FLAGS) \
		-m "integration or teardown" --junitxml=junit-integration.xml

list-stacks:
	$(PYTHON) sweep.py list

# NAMESPACE is required. An empty namespace exits non-zero rather than being read as
# "every run" — that is the unbounded failure mode, which would delete other runs'
# infrastructure and possibly infrastructure that is not a test run at all.
teardown-namespace:
	@if [ -z "$(NAMESPACE)" ]; then \
		echo "NAMESPACE is required. Refusing to treat an empty namespace as 'every run'." >&2; \
		echo "Usage: make teardown-namespace NAMESPACE=<namespace>" >&2; \
		exit 2; \
	fi
	IPA_IT_TEARDOWN=1 $(PYTHON) sweep.py teardown $(NAMESPACE)

clean:
	rm -rf .pytest_cache __pycache__
