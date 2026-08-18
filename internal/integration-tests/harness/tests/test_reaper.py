"""Offline tests for teardown ordering, namespace scoping, and the version purge.

Every assertion here is on **state reached or error raised**, never on a command
having been issued. The reference harness's most expensive bug was a test asserting
that ``aws s3 rm`` *ran* — which is exactly the assumption that failed, so it passed
against two broken runs.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

from harness import reaper
from harness import standing
from harness import sweep

# --------------------------------------------------------------------------- #
# Teardown ordering: nothing may tie with the logs rank
# --------------------------------------------------------------------------- #


def test_nothing_ties_with_the_logs_rank():
    """Python's sort is STABLE, so two entries sharing a rank keep input order.

    A tier tying with ``logs`` therefore deletes before it on some runs and after
    it on others, depending on how the stack listing happened to come back — and the
    run where it deletes first fails on a bucket still being written to.
    """
    ranks = {tier: sweep.tier_rank(f"ns-dev-{tier}") for tier in sweep.TIER_ORDER}
    ranks["<unknown>"] = sweep.tier_rank("ns-dev-somethingnew")
    logs_rank = sweep.tier_rank("ns-dev-logs")

    assert logs_rank == sweep.LOGS_RANK
    for tier, rank in ranks.items():
        assert rank != logs_rank, f"{tier} ties with logs at rank {rank}"


def test_logs_is_absent_from_tier_order():
    """Appending 'logs' to TIER_ORDER is the tempting form and is what creates the
    tie with an unknown tier."""
    assert "logs" not in sweep.TIER_ORDER


def test_unknown_tiers_sort_between_security_and_logs():
    unknown = sweep.tier_rank("ns-dev-brandnew")
    assert sweep.tier_rank("ns-dev-security") < unknown < sweep.tier_rank("ns-dev-logs")


def test_logs_sorts_last_for_every_input_permutation():
    stacks = [f"ns-dev-{t}" for t in ("logs", "frontend", "queue", "brandnew")]
    for perm in itertools.permutations(stacks):
        assert sweep.teardown_order(list(perm))[-1] == "ns-dev-logs"


def test_known_tiers_come_out_in_documented_order():
    stacks = [f"ns-dev-{t}" for t in reversed(sweep.TIER_ORDER)]
    ordered = sweep.teardown_order(stacks)
    assert ordered == [f"ns-dev-{t}" for t in sweep.TIER_ORDER]


# --------------------------------------------------------------------------- #
# Namespace scoping: pure, and never widening
# --------------------------------------------------------------------------- #

GROUPED = {
    "itaaa": ["itaaa-dev-frontend", "itaaa-dev-backend", "itaaa-dev-logs"],
    "itbbb": ["itbbb-dev-frontend", "itbbb-dev-queue"],
}


def test_selection_is_decidable_with_no_credentials():
    """A pure function over an already-retrieved listing, so the most dangerous
    behaviour in the system is testable without deleting anything."""
    assert sweep.select_namespaces(GROUPED, "itaaa") == {"itaaa": GROUPED["itaaa"]}


def test_a_teardown_scoped_to_one_namespace_names_no_stack_from_another():
    selected = sweep.select_namespaces(GROUPED, "itaaa")
    named = [s for stacks in selected.values() for s in stacks]
    assert not any(s.startswith("itbbb") for s in named)


def test_an_unmatched_namespace_selects_nothing():
    assert sweep.select_namespaces(GROUPED, "itzzz") == {}


def test_a_missing_namespace_does_not_select_everything_at_the_deleting_boundary(
    monkeypatch,
):
    """``select_namespaces`` passes a listing through when given no namespace, so the
    REFUSAL has to live at the deleting boundary — and that is what is asserted."""
    monkeypatch.setenv("IPA_IT_TEARDOWN", "1")
    deleted: list[str] = []
    monkeypatch.setattr(sweep, "_run", lambda *a, **k: deleted.append(a) or (True, ""))

    rc = sweep.cmd_teardown("us-east-1", namespace=None)

    assert rc != 0
    assert deleted == []


def test_teardown_refuses_without_the_environment_opt_in(monkeypatch):
    monkeypatch.delenv("IPA_IT_TEARDOWN", raising=False)
    deleted: list[str] = []
    monkeypatch.setattr(sweep, "_run", lambda *a, **k: deleted.append(a) or (True, ""))

    rc = sweep.cmd_teardown("us-east-1", namespace="itaaa")

    assert rc != 0
    assert deleted == []


def test_group_by_namespace_splits_on_the_env_marker():
    grouped = sweep.group_by_namespace(
        ["itaaa-dev-frontend", "itbbb-dev-logs", "unrelated-prod-thing"], env="dev"
    )
    assert set(grouped) == {"itaaa", "itbbb"}


# --------------------------------------------------------------------------- #
# The standing-resource pointer
# --------------------------------------------------------------------------- #


def test_pointer_is_removed_only_for_a_confirmed_deletion(monkeypatch, tmp_path):
    """Reference F5. A pointer surviving a successful teardown errs safe but teaches
    a reader to distrust the next pointer, which may be true."""
    monkeypatch.setattr(standing, "HERE", tmp_path)
    monkeypatch.setenv("IPA_IT_TEARDOWN", "1")

    p = standing.pointer_path("itaaa")
    p.write_text("standing\n")

    monkeypatch.setattr(
        sweep, "list_it_stacks", lambda *a, **k: (["itaaa-dev-frontend"], "")
    )
    monkeypatch.setattr(sweep, "_run", lambda *a, **k: (True, ""))

    sweep.cmd_teardown("us-east-1", "itaaa")

    assert not p.exists()


def test_pointer_survives_a_partial_teardown(monkeypatch, tmp_path):
    monkeypatch.setattr(standing, "HERE", tmp_path)
    monkeypatch.setenv("IPA_IT_TEARDOWN", "1")

    p = standing.pointer_path("itaaa")
    p.write_text("standing\n")

    monkeypatch.setattr(
        sweep, "list_it_stacks", lambda *a, **k: (["itaaa-dev-frontend"], "")
    )
    monkeypatch.setattr(sweep, "_run", lambda *a, **k: (False, "AccessDenied"))

    rc = sweep.cmd_teardown("us-east-1", "itaaa")

    assert rc != 0
    assert p.exists(), "a failed teardown must keep the only record of what stands"


def test_live_stacks_never_raises_and_reports_its_error(monkeypatch):
    """It runs at session teardown, where an exception would replace the
    standing-resource report with a fixture error."""

    def boom(*a, **k):
        raise OSError("credential chain exploded")

    monkeypatch.setattr(standing.subprocess, "run", boom)
    stacks, error = standing.live_stacks("itaaa", "us-east-1")

    assert stacks == []
    assert "credential chain exploded" in error


def test_pointer_text_is_readable_without_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(standing, "HERE", tmp_path)
    text = standing.render_pointer(
        "itaaa", "dev", "us-east-1", "sso", [("itaaa-dev-frontend", "CREATE_COMPLETE")]
    )
    assert "itaaa" in text
    assert "make teardown-namespace NAMESPACE=itaaa" in text
    assert "BILLABLE" in text


def test_parse_env_reads_one_file_with_no_run_folder_merge(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comment\nAPP_NAMESPACE=itaaa\nLOG_BUCKET_NAME='b'\nbroken\n")
    values = standing.parse_env(env)
    assert values == {"APP_NAMESPACE": "itaaa", "LOG_BUCKET_NAME": "b"}


# --------------------------------------------------------------------------- #
# The version purge
# --------------------------------------------------------------------------- #


def test_version_purge_drains_both_versions_and_delete_markers():
    """Draining only ``Versions`` leaves the delete markers, and ``DeleteBucket``
    refuses on markers alone."""
    calls: list[list[str]] = []
    pages = [
        json.dumps(
            {
                "Versions": [{"Key": "a", "VersionId": "v1"}],
                "DeleteMarkers": [{"Key": "a", "VersionId": "m1"}],
            }
        ),
        json.dumps({}),
    ]

    def runner(argv, timeout, cwd=None):
        calls.append(argv)
        if "list-object-versions" in argv:
            return True, pages.pop(0)
        return True, ""

    ok, detail = reaper.purge_versions("b", "us-east-1", runner=runner)

    assert ok
    assert "emptied (2 versions/markers removed)" in detail
    deleted = json.loads(
        next(a[a.index("--delete") + 1] for a in calls if "--delete" in a)
    )
    assert {o["VersionId"] for o in deleted["Objects"]} == {"v1", "m1"}


def test_a_failed_version_listing_does_not_report_emptied():
    """The reference's most expensive class of bug in miniature: a report that a
    command ran standing in for a state having been reached."""

    def runner(argv, timeout, cwd=None):
        if "list-object-versions" in argv:
            return False, "AccessDenied"
        return True, ""

    ok, detail = reaper.purge_versions("b", "us-east-1", runner=runner)

    assert ok is False
    assert "emptied" not in detail
    assert "AccessDenied" in detail


def test_purging_an_already_empty_bucket_is_a_no_op_not_an_error():
    ok, detail = reaper.purge_versions(
        "b", "us-east-1", runner=lambda *a, **k: (True, json.dumps({}))
    )
    assert ok
    assert "0 versions/markers removed" in detail


def test_empty_bucket_treats_the_purge_as_authoritative():
    """``aws s3 rm`` succeeding tells us nothing about whether ``DeleteBucket`` will:
    on a versioned bucket it leaves the bucket un-deletable while making it look
    empty."""

    def runner(argv, timeout, cwd=None):
        if "list-object-versions" in argv:
            return False, "listing blew up"
        return True, ""  # `s3 rm` "succeeds"

    ok, detail = reaper.empty_bucket("b", "us-east-1", runner=runner)

    assert ok is False
    assert "rm=ok" in detail


def test_version_purge_stops_at_the_page_cap_and_reports_rather_than_looping():
    def runner(argv, timeout, cwd=None):
        if "list-object-versions" in argv:
            return True, json.dumps({"Versions": [{"Key": "k", "VersionId": "v"}]})
        return True, ""

    ok, detail = reaper.purge_versions("b", "us-east-1", runner=runner)

    assert ok is False
    assert "still not empty" in detail


# --------------------------------------------------------------------------- #
# The reaper refuses what it cannot describe
# --------------------------------------------------------------------------- #


def test_reaper_refuses_when_deploy_mk_is_absent(tmp_path: Path):
    """Those artifacts encode the reverse ordering and the deletion waits. Without
    them the reaper would improvise an order against infrastructure it cannot
    describe."""
    with pytest.raises(reaper.ReaperRefused, match="deploy.mk is absent"):
        reaper.assert_reapable(tmp_path)


def test_reaper_accepts_a_project_carrying_deploy_mk(tmp_path: Path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "deploy.mk").write_text("deploy:\n\t@true\n")
    reaper.assert_reapable(tmp_path)  # must not raise


def test_reap_refuses_before_deleting_anything(tmp_path: Path):
    calls: list[list[str]] = []

    with pytest.raises(reaper.ReaperRefused):
        reaper.reap(
            tmp_path, "itaaa", "dev", "us-east-1",
            log_bucket="b",
            runner=lambda argv, t, cwd=None: calls.append(argv) or (True, ""),
        )

    assert calls == []


def test_reap_empties_the_log_bucket_twice(tmp_path: Path):
    """MAKEFILE_TEMPLATES.md states the log bucket keeps receiving CloudFront logs
    until the frontend stack is torn down, so a single pre-pass races against
    delivery that continues after it."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "deploy.mk").write_text("deploy:\n\t@true\n")

    def runner(argv, timeout, cwd=None):
        if "list-object-versions" in argv:
            return True, json.dumps({})
        return True, ""

    report = reaper.reap(
        tmp_path, "itaaa", "dev", "us-east-1",
        log_bucket="logs-b", runner=runner,
    )

    names = [s.name for s in report.steps]
    assert sum(1 for n in names if "logs-b" in n) == 2
    assert any("re-empty" in n for n in names)


def test_reap_deletes_the_security_stack(tmp_path: Path):
    """/ipa-destroy leaves it standing."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "deploy.mk").write_text("deploy:\n\t@true\n")

    report = reaper.reap(
        tmp_path, "itaaa", "dev", "us-east-1",
        runner=lambda argv, t, cwd=None: (True, ""),
    )

    assert any("itaaa-dev-security" in s.name for s in report.steps)
