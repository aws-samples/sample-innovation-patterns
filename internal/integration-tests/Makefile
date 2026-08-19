# IPA integration tests — maintainer-only harness.
#
# This is the UMBRELLA. It delegates scenario work to the scenario folders and owns only
# what belongs to no single scenario.
#
# Bare `make` prints help and creates nothing.

# VERBOSE trap, and it is worth stating because the obvious form is wrong:
#
#   WRONG: $(if $(VERBOSE),-vv -s,)
#
# Make's $(if) branches on NON-EMPTINESS, not truth. `VERBOSE=0` is non-empty, so that
# form turns verbosity ON when a user asked for it off. `filter-out` against a list of
# disabling words is what actually tests the value.
OFF := 0 no false off
VERBOSE ?= 1
PYTEST_FLAGS := $(if $(filter-out $(OFF),$(VERBOSE)),-vv -s -rs --log-cli-level=INFO,-q)

# `python -m pytest`, NOT bare `pytest`. `-m` places the working directory on sys.path,
# which is what makes `harness` importable with no build backend and no `pythonpath`
# entry. The bare `pytest` console script does NOT, and every module then fails with
# `ModuleNotFoundError: No module named 'harness'`. Measured, not assumed.
PYTHON      := uv run python
PYTEST      := uv run python -m pytest
NAMESPACE   ?=
IPA_IT_REGION ?= us-east-1
export IPA_IT_REGION

# Which scenario `test-ci` runs. Defaults to the CHEAP one, and that default is a SPEND
# DECISION rather than a convenience: `test-ci` is the name automation reaches for, so an
# unparameterised invocation costs about $1 here instead of about $15.
SCENARIO ?= compose

.DEFAULT_GOAL := help

.PHONY: help preflight test-offline test-compose test-deploy test-ci \
        list-stacks teardown-namespace clean

help:
	@echo ""
	@echo "IPA integration tests — maintainer-only. Nothing here runs in CI by itself."
	@echo ""
	@echo "  SCENARIOS  (each folder owns its own Makefile, cost and README)"
	@echo "    compose    /ipa-init + /ipa-compose, stops before /ipa-prepare."
	@echo "               MEASURED ~\$$0.94. Creates 1 free-but-real IAM stack."
	@echo "               make test-compose      (or: make -C compose test)"
	@echo "    deploy     FULL lifecycle. Deploys SEVEN stacks and LEAVES THEM"
	@echo "               STANDING. Cost UNMEASURED."
	@echo "               make test-deploy       (or: make -C deploy test)"
	@echo ""
	@echo "  FREE"
	@echo "    make test-offline        Shared-module regression suite, no credentials  (~5s, \$$0)"
	@echo "    make list-stacks         List standing integration-test stacks     (\$$0, read-only)"
	@echo ""
	@echo "  COSTS MONEY"
	@echo "    make preflight           Nine probes + Cognito check. Deploys and DELETES"
	@echo "                             two stacks under namespace 'itprobe'.    (cents)"
	@echo ""
	@echo "  REMOVES BILLABLE RESOURCES"
	@echo "    make teardown-namespace NAMESPACE=<ns>"
	@echo "                             Remove ONE run's stacks. NAMESPACE is required;"
	@echo "                             empty is never treated as 'every run'."
	@echo ""
	@echo "  CI SEAM"
	@echo "    make test-ci             Delegates to \$$(SCENARIO)/Makefile's test-ci."
	@echo "                             SCENARIO defaults to 'compose' (the cheap one)."
	@echo "                             make test-ci SCENARIO=deploy   # ~\$$15"
	@echo ""
	@echo "  Options"
	@echo "    VERBOSE=0                  Compact output (default is -vv -s)"
	@echo "    IPA_IT_NAMESPACE=<ns>      Pin the run namespace (validated at source)"
	@echo "    IPA_IT_STRICT_PREFLIGHT=1  Unmet prerequisites FAIL instead of skipping"
	@echo ""
	@echo "    IPA_IT_MAX_NUDGES=0        Do not push a drive that ends its turn early"
	@echo ""
	@echo "  Both scenarios last FAILED at composition (DECISIONS.md F3/F8). The cause is"
	@echo "  fixed in the skills; neither has been re-run, so neither is green yet."
	@echo ""

preflight:
	$(PYTHON) -m harness.preflight

test-offline:
	$(PYTEST) $(PYTEST_FLAGS) -c harness/tests/pytest.ini harness/tests/

test-compose:
	$(MAKE) -C compose test

test-deploy:
	$(MAKE) -C deploy test

# Refuses an unknown scenario BY NAME. Without this guard, `make test-ci SCENARIO=compse`
# reaches `make -C compse` and fails with "No such file or directory" — an error naming a
# missing directory rather than a mistyped scenario, which reads as a broken repository.
#
# Tests for the MAKEFILE, not the directory: a directory that exists but holds no Makefile
# is not a scenario either, and delegating into it produces a different confusing error
# for the same class of mistake.
test-ci:
	@if [ ! -f "$(SCENARIO)/Makefile" ]; then \
		echo "Unknown scenario '$(SCENARIO)'. Valid scenarios:" >&2; \
		ls -d */Makefile 2>/dev/null | sed 's|/Makefile||;s|^|  |' >&2; \
		exit 2; \
	fi
	$(MAKE) -C "$(SCENARIO)" test-ci

# list-stacks and teardown-namespace stay on the UMBRELLA, not in a scenario: a namespace
# sweep finds any run's stacks by prefix and belongs to no single scenario. Putting them in
# one would mean cleaning up after `deploy` required invoking `compose`.
list-stacks:
	$(PYTHON) -m harness.sweep list

# NAMESPACE is required. An empty namespace exits non-zero rather than being read as
# "every run" — that is the unbounded failure mode, which would delete other runs'
# infrastructure and possibly infrastructure that is not a test run at all.
teardown-namespace:
	@if [ -z "$(NAMESPACE)" ]; then \
		echo "NAMESPACE is required. Refusing to treat an empty namespace as 'every run'." >&2; \
		echo "Usage: make teardown-namespace NAMESPACE=<namespace>" >&2; \
		exit 2; \
	fi
	IPA_IT_TEARDOWN=1 $(PYTHON) -m harness.sweep teardown $(NAMESPACE)

clean:
	$(MAKE) -C compose clean
	$(MAKE) -C deploy clean
	rm -rf .pytest_cache __pycache__ harness/__pycache__ harness/tests/__pycache__
