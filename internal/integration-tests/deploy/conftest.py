"""The deploy scenario's own drive. Everything else comes from ``harness.fixtures``.

``deploy_run`` is the fixture ``test_deploy.py`` has always requested and that nothing
ever defined. Its absence did not make this tier merely unrun -- it made it
**uncollectable**: `--setup-plan` failed with eight setup errors before any preflight
probe executed, so the failure named neither a missing credential nor a stopped daemon.
That stayed invisible because the routine free target deselects these markers.
"""

from __future__ import annotations

import asyncio

import pytest

from harness import driver
from harness.fixtures import _unmet


@pytest.fixture(scope="session")
def deploy_run(temp_project, resolver, transcript):
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
    """
    _unmet("bedrock_driver_model", "docker_daemon", "npm_present")
    options = driver.full_lifecycle_options(temp_project.root, resolver, transcript)
    result = asyncio.run(
        driver.drive(
            driver.FULL_PROMPT, temp_project.root, resolver, transcript, options
        )
    )
    # Printed because a run of this length has no other progress output, and a wedged
    # twenty-minute billable run with a blank screen is not recoverable by re-running it.
    print(
        f"\ndeploy drive: cost=${result.cost_usd} turns={result.turns} "
        f"wall={result.wall_clock_s:.0f}s"
    )
    return result
