"""Has the lifecycle actually finished? Answered from disk and AWS, never from the agent.

``ResultMessage(subtype='success', stop_reason='end_turn')`` is what the SDK reports for
a drive that stopped a tenth of the way through ``/ipa-compose`` — measured twice, at the
same boundary, where compose delegates to ``/ipa-security``. So the run's own account of
itself cannot be the completion signal, and these predicates read the artifacts on disk
and the stacks in the account instead.

**Here rather than in each scenario's ``conftest.py``** because a scenario conftest is
not reachable by the offline suite, and these are the functions that decide whether a
billable run gets re-queried and whether twenty-one assertions run against nothing. They
are pure enough to test for free: one takes a path, the other takes a lister.
"""

from __future__ import annotations

from pathlib import Path

from harness import artifacts, standing


def compose_state(project: Path) -> tuple[bool, str]:
    """``(finished, what_is_missing)`` for the compose scope.

    Presence on disk is the whole test. An agent that stopped early cannot report
    artifacts it did not write, which is exactly what makes this a usable signal where
    ``subtype='success'`` is not.
    """
    missing = artifacts.missing_artifacts(project)
    if not missing:
        return True, ""
    return False, (
        f"{len(missing)} of /ipa-compose's {len(artifacts.EXPECTED_ARTIFACTS)} "
        f"artifacts are still absent ({', '.join(missing)}), so composition is "
        "unfinished."
    )


def deploy_state(
    project: Path,
    namespace: str,
    env: str,
    region: str,
    *,
    strict: bool = False,
    lister=standing.live_stacks,
) -> tuple[bool, str]:
    """``(finished, what_is_missing)`` for the full lifecycle.

    Both halves are load-bearing. Artifacts alone would call a composed-but-undeployed
    project finished; stacks alone would be blind to a deployment made by hand.

    ``strict`` decides what an ERRORED stack listing means, and the two callers need
    opposite answers from the same three-way state — listed, empty, unknown:

    *   The nudge decision (``strict=False``) treats unknown as finished. Re-querying the
        agent because a credential blip broke one ``list-stacks`` spends money on a
        deployment that may already be complete.
    *   The gate (``strict=True``) treats unknown as a failure. Passing on an errored
        listing lets the twenty-one downstream assertions fail one at a time against
        nothing, which is the whole thing the gate exists to prevent.

    ``lister`` is injected so the offline suite can exercise all three states without a
    credential; nothing in the scenarios passes it.
    """
    done, missing = compose_state(project)
    if not done:
        return False, f"{missing} Nothing could have been deployed."

    live, error = lister(namespace, region)
    if error:
        if not strict:
            return True, ""
        return False, (
            f"could not list stacks under {namespace!r}, so whether the deployment "
            f"completed is unknown: {error}"
        )

    found = sorted(name for name, _ in live)
    absent = standing.absent_tiers(namespace, env, found)
    if absent:
        return False, (
            f"{len(absent)} of {len(standing.EXPECTED_TIERS)} stacks are not deployed "
            f"({', '.join(absent)}); live under {namespace!r}: {found or 'none'}."
        )
    return True, ""
