"""The nudge loop, and the billable/free classification of a standing stack.

Both behaviours exist because of one measured failure (2026-08-18): a drive ended its
turn a tenth of the way through ``/ipa-compose``, reported
``ResultMessage(subtype='success')``, and left exactly one free IAM stack standing.
Twenty-one assertions then failed on ``describe_stacks`` for stacks nothing created,
and the standing-resource report called the one IAM stack BILLABLE.

These tests are free and offline: the SDK client is replaced with a fake, so the loop's
control flow -- how many times it re-queries, when it refuses to -- is checked without a
session, a credential or a cent.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from harness import answers, artifacts, driver, lifecycle, standing


# --------------------------------------------------------------------------- #
# A fake SDK client
# --------------------------------------------------------------------------- #


@dataclass
class _FakeResult:
    """Stands in for ``ResultMessage``. Matched by CLASS NAME in ``drive``."""

    subtype: str = "success"
    total_cost_usd: float = 0.5
    num_turns: int = 7


# ``drive`` dispatches on ``type(message).__name__``, so the fake must carry the real
# name. Renaming rather than subclassing keeps the SDK out of this test entirely --
# which is the point: the offline tier must run on a checkout with no extras installed.
_FakeResult.__name__ = "ResultMessage"


class _FakeClient:
    """Records every prompt it is queried with; yields one result per query."""

    def __init__(self, options=None) -> None:
        self.options = options
        self.prompts: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def query(self, prompt: str) -> None:
        self.prompts.append(prompt)

    async def receive_response(self):
        yield _FakeResult()


@pytest.fixture
def fake_client(monkeypatch):
    """Install one fake client and hand it back so its prompts can be inspected."""
    created: list[_FakeClient] = []

    def factory(options=None):
        client = _FakeClient(options)
        created.append(client)
        return client

    monkeypatch.setattr(driver, "ClaudeSDKClient", factory)
    return created


@pytest.fixture
def transcript(tmp_path):
    return driver.Transcript(path=tmp_path / "t.jsonl")


@pytest.fixture
def resolver():
    return answers.AnswerResolver(namespace="itaaaaaaaa", profile="p")


def _drive(transcript, resolver, tmp_path, **kwargs):
    """Run ``drive`` with options already built, so no SDK is needed."""
    return asyncio.run(
        driver.drive(
            "go", tmp_path, resolver, transcript, options=_FakeOptions(), **kwargs
        )
    )


@dataclass
class _FakeOptions:
    """Only the two fields ``drive`` records at ``run_start``."""

    max_budget_usd: float = 5.0
    max_turns: int = 300


# --------------------------------------------------------------------------- #
# The loop
# --------------------------------------------------------------------------- #


def test_a_complete_drive_is_never_nudged(fake_client, transcript, resolver, tmp_path):
    result = _drive(
        transcript, resolver, tmp_path, is_complete=lambda _r: (True, "")
    )
    assert result.nudges == 0
    assert result.incomplete_reason == ""
    assert fake_client[0].prompts == ["go"]


def test_no_predicate_means_no_nudge(fake_client, transcript, resolver, tmp_path):
    """Absent a definition of "finished", the drive must not invent one.

    Nudging by default would re-query every scenario that has not opted in, and each
    re-query costs money on the billable path.
    """
    result = _drive(transcript, resolver, tmp_path)
    assert result.nudges == 0
    assert fake_client[0].prompts == ["go"]


def test_an_unfinished_drive_is_nudged_up_to_the_cap(
    fake_client, transcript, resolver, tmp_path
):
    result = _drive(
        transcript,
        resolver,
        tmp_path,
        is_complete=lambda _r: (False, "scripts/deploy.mk is absent"),
        max_nudges=2,
    )
    assert result.nudges == 2
    # One original prompt plus one per nudge -- the cap bounds the spend.
    assert len(fake_client[0].prompts) == 3
    assert "scripts/deploy.mk is absent" in fake_client[0].prompts[1]
    assert result.incomplete_reason == "scripts/deploy.mk is absent"


def test_the_nudge_states_what_is_missing_not_merely_continue(
    fake_client, transcript, resolver, tmp_path
):
    """The agent has just reported success; it needs the specific gap.

    A bare "continue" invites it to re-run the step it thinks it finished, which on the
    deploy path means a second composition over a half-composed project.
    """
    _drive(
        transcript,
        resolver,
        tmp_path,
        is_complete=lambda _r: (False, "4 of 7 stacks are not deployed"),
        max_nudges=1,
    )
    nudge = fake_client[0].prompts[1]
    assert "4 of 7 stacks are not deployed" in nudge
    assert "Do not start over" in nudge


def test_a_ceiling_stop_is_never_nudged(
    fake_client, transcript, resolver, tmp_path, monkeypatch
):
    """Spending more on a run already stopped for spending is the one case where
    continuing is certainly wrong."""

    class _Stopped(_FakeResult):
        pass

    _Stopped.__name__ = "ResultMessage"

    async def receive(self):
        yield _Stopped(subtype="error_max_budget_usd")

    monkeypatch.setattr(_FakeClient, "receive_response", receive)

    result = _drive(
        transcript, resolver, tmp_path, is_complete=lambda _r: (False, "unfinished")
    )
    assert result.stopped_by_ceiling
    assert result.nudges == 0
    assert fake_client[0].prompts == ["go"]


def test_nudges_are_recorded_in_the_transcript(
    fake_client, transcript, resolver, tmp_path
):
    """A run that only completed because it was pushed must say so in the record --
    the transcript outlives both the terminal and the temp project."""
    _drive(
        transcript,
        resolver,
        tmp_path,
        is_complete=lambda _r: (False, "still composing"),
        max_nudges=1,
    )
    lines = transcript.path.read_text()
    assert '"kind": "nudge"' in lines
    assert '"kind": "nudge_exhausted"' in lines
    assert "still composing" in lines


# --------------------------------------------------------------------------- #
# Billable vs free
# --------------------------------------------------------------------------- #


def test_only_the_security_tier_counts_as_free():
    stacks = [
        ("itaaa-dev-security", "CREATE_COMPLETE"),
        ("itaaa-dev-frontend", "CREATE_COMPLETE"),
    ]
    assert standing.billable(stacks) == [("itaaa-dev-frontend", "CREATE_COMPLETE")]


def test_an_unrecognised_tier_counts_as_billable():
    """The safe direction: an unknown stack under the run's namespace is likelier a
    tier this table has not been taught than a second free IAM stack."""
    assert standing.billable([("itaaa-dev-whatever", "CREATE_COMPLETE")])


def test_the_pointer_does_not_call_an_iam_only_run_billable(tmp_path, monkeypatch):
    monkeypatch.setattr(standing, "HERE", tmp_path)
    text = standing.render_pointer(
        "itaaa", "dev", "us-east-1", "sso", [("itaaa-dev-security", "CREATE_COMPLETE")]
    )
    assert "Nothing standing here is billable" in text
    assert "IAM only, not billable" in text
    # Still names the way out: the namespace must be free for the next run.
    assert "make teardown-namespace NAMESPACE=itaaa" in text


def test_absent_tiers_names_what_is_missing():
    absent = standing.absent_tiers("itaaa", "dev", ["itaaa-dev-security"])
    assert "frontend" in absent
    assert "security" not in absent
    assert len(absent) == len(standing.EXPECTED_TIERS) - 1


# --------------------------------------------------------------------------- #
# What "finished" means
# --------------------------------------------------------------------------- #


def _compose(project):
    """A project whose eight artifacts all exist."""
    (project / "scripts").mkdir(parents=True, exist_ok=True)
    for rel in artifacts.EXPECTED_ARTIFACTS:
        (project / rel).write_text("x\n")
    return project


def _all_seven(namespace):
    return [
        (f"{namespace}-dev-{tier}", "CREATE_COMPLETE")
        for tier in standing.EXPECTED_TIERS
    ]


def test_compose_is_unfinished_until_every_artifact_exists(tmp_path):
    done, missing = lifecycle.compose_state(tmp_path)
    assert not done
    assert "artifacts are still absent" in missing
    assert "scripts/deploy.mk" in missing

    done, missing = lifecycle.compose_state(_compose(tmp_path))
    assert done and missing == ""


def test_deploy_is_unfinished_when_composition_is(tmp_path):
    """Reported as a composition gap, not as absent stacks.

    The naming matters more than the boolean: "4 of 7 stacks are not deployed" sends a
    reader to CloudFormation, when what happened is that no Makefile was ever written.
    """
    done, missing = lifecycle.deploy_state(
        tmp_path, "itaaa", "dev", "us-east-1", lister=lambda *a: ([], "")
    )
    assert not done
    assert "artifacts are still absent" in missing
    assert "Nothing could have been deployed" in missing


def test_deploy_is_unfinished_when_stacks_are_missing(tmp_path):
    done, missing = lifecycle.deploy_state(
        _compose(tmp_path),
        "itaaa",
        "dev",
        "us-east-1",
        lister=lambda *a: ([("itaaa-dev-security", "CREATE_COMPLETE")], ""),
    )
    assert not done
    assert "6 of 7 stacks are not deployed" in missing
    assert "frontend" in missing


def test_deploy_is_finished_with_all_seven(tmp_path):
    done, missing = lifecycle.deploy_state(
        _compose(tmp_path),
        "itaaa",
        "dev",
        "us-east-1",
        lister=lambda *a: (_all_seven("itaaa"), ""),
    )
    assert done and missing == ""


def test_an_errored_listing_is_finished_for_the_nudge_and_a_failure_for_the_gate(
    tmp_path,
):
    """The same three-way state, opposite answers, and both are deliberate.

    Nudging on an unknown listing spends money re-querying a deployment that may be
    complete; passing the gate on one lets twenty-one assertions fail against nothing.
    """
    project = _compose(tmp_path)

    def broken(*_args):
        return [], "ExpiredToken"

    done, missing = lifecycle.deploy_state(
        project, "itaaa", "dev", "us-east-1", lister=broken
    )
    assert done and missing == ""

    done, missing = lifecycle.deploy_state(
        project, "itaaa", "dev", "us-east-1", strict=True, lister=broken
    )
    assert not done
    assert "ExpiredToken" in missing
    assert "unknown" in missing
