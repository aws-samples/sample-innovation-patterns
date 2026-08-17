"""Fixtures for the billable tiers, and the two rules that keep them safe.

**One ``_unmet`` helper decides every prerequisite.** It imports ``preflight.py``, so
a probe added there takes effect everywhere without any test being edited. A check
duplicated in a second place is one a later-added probe can be forgotten from, and
the consequence is asymmetric: a skip is right on a maintainer's laptop, where a
stopped Docker daemon is an environment gap rather than a defect in the code under
test, and **catastrophic in a pipeline, where a build that skips every billable test
exits 0 having tested nothing**. ``IPA_IT_STRICT_PREFLIGHT`` flips that one helper.

**The preservation rule is the single most consequential thing in this file.** The
temp project is preserved when the run's stacks are STANDING — never on the basis of
tests passing — and it is preserved when the standing check itself errors. The temp
project holds ``.env`` and ``scripts/*.mk``, the only documented means of teardown, so
deleting them after a passing run whose stacks still stand removes the mechanism for
removing what is still costing money. And a listing that errors is exactly the case
where standing stacks are most likely: the same credential or network fault may have
broken the teardown too.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

import answers
import driver
import preflight
import standing
import workspace

REGION = preflight.REGION
ENV = "dev"


# --------------------------------------------------------------------------- #
# The ONE prerequisite helper
# --------------------------------------------------------------------------- #


def _strict() -> bool:
    return os.environ.get("IPA_IT_STRICT_PREFLIGHT") == "1"


def _unmet(*probe_names: str) -> None:
    """Skip -- or, under strict mode, FAIL -- when any named probe reports negative.

    The single decision point. Nothing else in the harness reads
    ``IPA_IT_STRICT_PREFLIGHT``, and no test writes its own probe check.
    """
    for name in probe_names:
        ok, detail = preflight.run_probe(name)
        if ok:
            continue
        message = f"prerequisite {name!r} unmet: {detail}"
        if _strict():
            pytest.fail(f"{message} (IPA_IT_STRICT_PREFLIGHT=1)")
        pytest.skip(message)


# --------------------------------------------------------------------------- #
# Session fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def aws_profile() -> str:
    _unmet("aws_profile_resolvable", "sts_caller_identity")
    return workspace.resolve_aws_profile() or preflight.PROFILE


@pytest.fixture(scope="session")
def resolver(aws_profile: str) -> answers.AnswerResolver:
    """One resolver per session, so deploy and teardown share a namespace.

    ``IPA_IT_NAMESPACE`` is passed THROUGH ``make_namespace`` (inside
    ``AnswerResolver``), which is what validates an injected value -- the assertions
    live in the generator, so a caller writing ``injected or generate()`` would never
    check it.
    """
    return answers.resolver_from_env(profile=aws_profile)


@pytest.fixture(scope="session")
def namespace(resolver: answers.AnswerResolver) -> str:
    return resolver.namespace


@pytest.fixture(scope="session")
def transcript(namespace: str, tmp_path_factory) -> driver.Transcript:
    path = Path(__file__).resolve().parent / f"transcript-{namespace}.jsonl"
    return driver.Transcript(path=path)


@pytest.fixture(scope="session")
def temp_project(
    resolver: answers.AnswerResolver,
    namespace: str,
    aws_profile: str,
    transcript: driver.Transcript,
    tmp_path_factory,
):
    """Build the temp project, then apply the preservation rule at teardown."""
    _unmet("claude_agent_sdk_importable", "docker_daemon", "npm_present", "uv_present")

    dest = tmp_path_factory.mktemp("ipa-project", numbered=True) / "project"
    source = workspace.build(dest)
    transcript.record_source(source)
    print(f"\ntemp project: {source.describe()}")

    yield source

    # --- The preservation rule ------------------------------------------------
    # Based on STACKS STANDING, never on tests passing. Fail-safe: preserve when the
    # listing itself errors.
    stacks, error = standing.live_stacks(namespace, aws_profile, REGION)

    if error:
        print(
            f"\nPRESERVING {source.root}: could not determine whether stacks are "
            f"standing ({error}). Preserving on an errored listing is deliberate -- "
            "it is exactly the case where standing stacks are most likely."
        )
        return

    if stacks:
        env_values = standing.parse_env(source.root / ".env")
        standing.report_everywhere(
            namespace, ENV, REGION, aws_profile, stacks, env_values,
            redact=transcript.redact,
        )
        print(
            f"PRESERVING {source.root}: it holds .env and scripts/*.mk, the only "
            "documented means of teardown."
        )
        return

    # Nothing standing -- safe to remove regardless of whether tests passed.
    shutil.rmtree(source.root, ignore_errors=True)
    print(f"\nno stacks standing under {namespace}; removed {source.root}")


@pytest.fixture(scope="session")
def compose_run(temp_project, resolver, transcript):
    """Drive the agent as far as ``/ipa-compose``'s completion report."""
    import asyncio

    _unmet("bedrock_driver_model")
    options = driver.build_options(temp_project.root, resolver, transcript)
    result = asyncio.run(
        driver.drive(
            driver.COMPOSE_PROMPT, temp_project.root, resolver, transcript, options
        )
    )
    print(
        f"\ncompose drive: cost=${result.cost_usd} turns={result.turns} "
        f"wall={result.wall_clock_s:.0f}s channels={sorted(result.channels_used)}"
    )
    return result


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Expose each phase's outcome on the item.

    Only collected from a conftest, which is why it lives here. Note that nothing in
    the preservation rule consults it -- preservation is decided by standing stacks,
    deliberately not by test outcomes.
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"report_{report.when}", report)
