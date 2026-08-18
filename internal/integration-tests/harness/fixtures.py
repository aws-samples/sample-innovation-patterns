"""Session fixtures shared by every scenario, plus the two rules that keep them safe.

Loaded as a **pytest plugin** (``-p harness.fixtures`` in each scenario's ``pytest.ini``),
not imported and not copied. Three reasons, in increasing order of importance:

*   ``pytest_runtest_makereport`` is a hook, and pytest collects hooks from ``conftest.py``
    files and from plugins -- never from an ordinary imported module.
*   Copying would mean each scenario carries its own drift-prone duplicate.
*   **The preservation rule below decides whether to delete the only documented means of
    teardown.** Two copies of that rule will diverge, and the divergence nobody notices
    is the one that deletes more.

**One ``_unmet`` helper decides every prerequisite.** It imports ``preflight``, so a probe
added there takes effect everywhere without any test being edited. A check duplicated in a
second place is one a later-added probe can be forgotten from, and the consequence is
asymmetric: a skip is right on a maintainer's laptop, where a stopped Docker daemon is an
environment gap rather than a defect in the code under test, and **catastrophic in a
pipeline, where a build that skips every billable test exits 0 having tested nothing**.
``IPA_IT_STRICT_PREFLIGHT`` flips that one helper.

**The preservation rule is the single most consequential thing in this file.** The temp
project is preserved when the run's stacks are STANDING -- never on the basis of tests
passing -- and it is preserved when the standing check itself errors. The temp project
holds ``.env`` and ``scripts/*.mk``, the only documented means of teardown, so deleting
them after a passing run whose stacks still stand removes the mechanism for removing what
is still costing money. And a listing that errors is exactly the case where standing
stacks are most likely: the same credential or network fault may have broken the teardown
too.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from harness import answers, aws, driver, preflight, standing, workspace

REGION = aws.REGION
ENV = "dev"

#: The harness root -- one level above this module. Run artifacts land HERE, not inside
#: ``harness/``: ``.gitignore``'s globs, ``README.md`` and the deployed buildspec's
#: artifact paths all name this location, and none of them fails loudly if it moves.
HARNESS_ROOT = Path(__file__).resolve().parents[1]


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
def credentials() -> str:
    """The credential RESOLUTION METHOD, not a profile name.

    Was ``aws_profile``, and the rename is the point: the harness authenticates from the
    default credential chain, so what there is to report is which link answered --
    ``env``, ``sso``, ``container-role``, ``iam-role``. Anything needing a profile
    *name* wants ``harness.aws.profile_for_env`` instead, which answers a different
    question and is never used to build a session.
    """
    _unmet("credentials_resolvable", "sts_caller_identity")
    creds = aws.session().get_credentials()
    return getattr(creds, "method", "unknown")


@pytest.fixture(scope="session")
def resolver(credentials: str) -> answers.AnswerResolver:
    """One resolver per session, so deploy and teardown share a namespace.

    ``IPA_IT_NAMESPACE`` is passed THROUGH ``make_namespace`` (inside
    ``AnswerResolver``), which is what validates an injected value -- the assertions live
    in the generator, so a caller writing ``injected or generate()`` would never check
    it.

    Depends on ``credentials`` for ORDERING, not for its value: the credential probes
    must gate the session before anything drives an agent. The profile the resolver
    carries comes from ``AWS_PROFILE`` via ``resolver_from_env``, which raises when it is
    unset.
    """
    return answers.resolver_from_env()


@pytest.fixture(scope="session")
def namespace(resolver: answers.AnswerResolver) -> str:
    return resolver.namespace


@pytest.fixture(scope="session")
def transcript(namespace: str, tmp_path_factory) -> driver.Transcript:
    path = HARNESS_ROOT / f"transcript-{namespace}.jsonl"
    return driver.Transcript(path=path)


@pytest.fixture(scope="session")
def temp_project(
    resolver: answers.AnswerResolver,
    namespace: str,
    credentials: str,
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
    stacks, error = standing.live_stacks(namespace, REGION)

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
            namespace, ENV, REGION, credentials, stacks, env_values,
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


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Expose each phase's outcome on the item.

    Collected because this module is loaded as a PLUGIN -- an ordinary imported module's
    hooks are never registered. Note that nothing in the preservation rule consults it:
    preservation is decided by standing stacks, deliberately not by test outcomes.
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"report_{report.when}", report)
