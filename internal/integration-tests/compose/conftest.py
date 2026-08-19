"""The compose scenario's own drive. Everything else comes from ``harness.fixtures``.

``compose_run`` is defined HERE rather than in the shared harness because the drive's
scope and prompt are what make this scenario what it is -- a scenario is its drive. Put
it in the shared layer and the shared layer would have to know about each scenario,
which inverts the dependency the package exists to create.

It is also **the thing in this folder that spends money**, which is why it is read in the
same directory as the README stating what that costs.
"""

from __future__ import annotations

import asyncio

import pytest

from harness import driver, lifecycle
from harness.fixtures import _unmet


@pytest.fixture(scope="session")
def compose_run(temp_project, resolver, transcript):
    """Drive the agent as far as ``/ipa-compose``'s completion report."""
    _unmet("bedrock_driver_model")
    options = driver.build_options(temp_project.root, resolver, transcript)
    result = asyncio.run(
        driver.drive(
            driver.COMPOSE_PROMPT,
            temp_project.root,
            resolver,
            transcript,
            options,
            # What "finished" means lives in harness.lifecycle: the artifacts on disk,
            # never the run's own report. ``subtype='success'`` is what the SDK says
            # about a turn that ended, and compose has twice ended its turn at Step 1.5
            # -- after delegating to /ipa-security -- with every artifact ungenerated.
            is_complete=lambda _r: lifecycle.compose_state(temp_project.root),
        )
    )
    # Printed because a drive of this length has no other progress output, and a wedged
    # run with a blank screen is indistinguishable from a slow one.
    print(
        f"\ncompose drive: cost=${result.cost_usd} turns={result.turns} "
        f"wall={result.wall_clock_s:.0f}s channels={sorted(result.channels_used)} "
        f"nudges={result.nudges}"
    )
    return result
