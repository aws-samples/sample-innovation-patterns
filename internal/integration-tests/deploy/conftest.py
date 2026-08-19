"""The deploy scenario's own drive. Everything else comes from ``harness.fixtures``.

``deploy_run`` is the fixture ``test_deploy.py`` has always requested and that nothing
ever defined. Its absence did not make this tier merely unrun -- it made it
**uncollectable**: `--setup-plan` failed with eight setup errors before any preflight
probe executed, so the failure named neither a missing credential nor a stopped daemon.
That stayed invisible because the routine free target deselects these markers.

**The completion gate is the other thing this file exists for.** A drive that ends its
turn early reports ``ResultMessage(subtype='success')``, and every assertion downstream
then fails on its own terms -- ``describe_stacks`` on a stack nothing created,
twenty-one times, in a ``botocore`` traceback that mentions neither ``/ipa-compose`` nor
the turn that ended. Measured 2026-08-18: fifteen failures and six errors, not one of
which named the cause. The gate turns that into one message, before any test runs, at
the point where the run's own artifacts are the evidence.

What "finished" MEANS lives in ``harness.lifecycle``, not here: a scenario conftest is
unreachable from the offline suite, and the predicate that decides whether a billable run
is re-queried is not something to leave untested.
"""

from __future__ import annotations

import asyncio

import pytest

from harness import aws, driver, lifecycle
from harness.fixtures import _unmet

#: The environment every stack name carries. ``harness.fixtures`` uses the same value
#: for the standing-resource report.
ENV = "dev"


@pytest.fixture(scope="session")
def deploy_run(temp_project, resolver, transcript, namespace):
    """FULL LIFECYCLE. Creates billable AWS resources and LEAVES THEM STANDING.

    **Session scope is required, not preferred.** At module scope this drives twice --
    once for ``test_deploy.py`` and once for ``test_teardown.py`` -- which doubles both
    the spend and the standing infrastructure. Worse, the teardown would then remove the
    *second* deployment while the assertions verified the *first*, so the run reports a
    successful verify-then-remove while the deployment it actually checked stays up and
    billing. That is the exact failure the verify-before-remove ordering exists to
    prevent, reintroduced through fixture scope instead of through invocation count.

    The session-scoped ``resolver`` in ``harness.fixtures`` is the matching half: it is
    what makes deploy and teardown share one namespace without threading it.

    The gate at the end **fails this fixture rather than each assertion**, so a
    truncated lifecycle reports once and accurately. It is safe to fail here:
    ``test_teardown.py`` depends on ``namespace`` and ``temp_project``, never on this
    fixture, so the teardown path and the standing-resource report both still run.
    """
    _unmet("bedrock_driver_model", "docker_daemon", "npm_present")
    options = driver.full_lifecycle_options(temp_project.root, resolver, transcript)
    result = asyncio.run(
        driver.drive(
            driver.FULL_PROMPT,
            temp_project.root,
            resolver,
            transcript,
            options,
            is_complete=lambda _r: lifecycle.deploy_state(
                temp_project.root, namespace, ENV, aws.REGION
            ),
        )
    )
    # Printed because a run of this length has no other progress output, and a wedged
    # twenty-minute billable run with a blank screen is not recoverable by re-running it.
    print(
        f"\ndeploy drive: cost=${result.cost_usd} turns={result.turns} "
        f"wall={result.wall_clock_s:.0f}s nudges={result.nudges}"
    )

    assert not result.stopped_by_ceiling, (
        f"a ceiling stopped the run rather than the agent finishing: "
        f"cost=${result.cost_usd} turns={result.turns}. Raising "
        "IPA_IT_FULL_MAX_BUDGET_USD is the wrong first move -- read the transcript "
        "for what it was doing when it ran out."
    )

    finished, missing = lifecycle.deploy_state(
        temp_project.root, namespace, ENV, aws.REGION, strict=True
    )
    assert finished, (
        f"the lifecycle did not complete, so the assertions below have nothing to "
        f"assert against: {missing}\n"
        f"nudges={result.nudges}, gates seen={sorted(set(result.gates_seen))}, "
        f"transcript={transcript.path}.\n"
        "A run that ends its turn mid-lifecycle reports subtype='success', which is "
        "why this is checked against disk and AWS rather than against the result."
    )

    # Not fatal, and stated anyway: the run completed, and it needed help to. Every
    # nudge is a skill that stopped where it should have continued.
    if result.nudges:
        print(
            f"\nthe lifecycle completed only after {result.nudges} nudge(s). "
            f"Last gap: {missing or '(none at the final check)'}. A skill ended its "
            "turn early -- see the transcript's 'nudge' events for where."
        )

    return result
