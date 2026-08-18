"""Verify-then-remove, behind a two-part opt-in.

Gated on **both** the ``teardown`` marker and ``IPA_IT_TEARDOWN=1``. One opt-in is
satisfiable by accident: a pipeline-level variable applies to every phase of every
build, and a marker alone is satisfied by a wildcard test selection.

The verify-before-remove step is **ordering, not coverage**. Without it, a run that
provisioned nothing and a run that provisioned everything both end with an empty
account and a passing teardown — so the check would report success in exactly the case
where the deployment it was meant to remove never existed.
"""

from __future__ import annotations

import os

import pytest

from harness import aws, reaper, standing, sweep

pytestmark = pytest.mark.teardown

OTHER_NAMESPACE_SENTINEL = "itnotthisrun"


@pytest.fixture(scope="module", autouse=True)
def require_second_opt_in():
    """The environment opt-in. The marker is the first; this is the second."""
    if os.environ.get("IPA_IT_TEARDOWN") != "1":
        pytest.skip(
            "IPA_IT_TEARDOWN=1 is not set. Teardown requires two independent "
            "opt-ins, because one is satisfiable by accident."
        )


def test_the_deployment_is_live_before_anything_is_removed(namespace, temp_project):
    """Ordering, not coverage — see the module docstring.

    Runs first in file order, so a namespace under which nothing was deployed fails
    here rather than passing as a successful teardown of nothing.
    """
    stacks, error = standing.live_stacks(namespace, aws.REGION)
    assert not error, f"could not verify the deployment: {error}"
    assert stacks, (
        f"nothing is deployed under {namespace!r}, so there is nothing to tear down. "
        "This fails rather than passing: a run that provisioned nothing and a run "
        "that provisioned everything otherwise both end with a passing teardown."
    )
    print(f"\nverified live before teardown: {len(stacks)} stack(s) under {namespace}")


def test_teardown_removes_this_run(namespace, temp_project):
    """Run the reaper, which supplies the three steps IPA's skills refuse to take."""
    env_values = standing.parse_env(temp_project.root / ".env")
    report = reaper.reap(
        project=temp_project.root,
        namespace=namespace,
        env="dev",
        region=aws.REGION,
        log_bucket=env_values.get("LOG_BUCKET_NAME"),
        site_bucket=env_values.get("SITE_BUCKET_NAME") or env_values.get("APP_BUCKET_NAME"),
        ecr_repository=env_values.get("ECR_REPOSITORY_NAME"),
    )
    print("\n" + report.render())
    assert report.ok, f"teardown did not complete cleanly:\n{report.render()}"


def test_no_stack_remains_under_this_namespace(namespace):
    stacks, error = standing.live_stacks(namespace, aws.REGION)
    assert not error, f"could not confirm removal: {error}"
    assert stacks == [], f"stacks still standing under {namespace}: {stacks}"


def test_no_other_run_was_removed(namespace):
    """Cannot be inferred from the previous assertion.

    A teardown that deleted everything in the account satisfies "nothing remains under
    this namespace" perfectly, so that assertion alone cannot distinguish correct
    scoping from unbounded deletion. This checks the scoping logic directly, against a
    listing that includes another namespace.
    """
    names, error = sweep.list_it_stacks(aws.REGION)
    assert not error, f"could not list stacks: {error}"

    grouped = sweep.group_by_namespace(names)
    grouped.setdefault(OTHER_NAMESPACE_SENTINEL, [f"{OTHER_NAMESPACE_SENTINEL}-dev-frontend"])

    selected = sweep.select_namespaces(grouped, namespace)
    named = [s for stacks in selected.values() for s in stacks]

    assert not any(s.startswith(OTHER_NAMESPACE_SENTINEL) for s in named), (
        f"teardown scoped to {namespace!r} selected a stack from another namespace: "
        f"{named}"
    )


def test_the_standing_resource_pointer_was_removed(namespace):
    """Removed only for a confirmed deletion (reference F5).

    Reached only after the removal assertions above passed, so a pointer surviving
    here would mean a confirmed teardown left a stale claim that stacks stand.
    """
    path = standing.pointer_path(namespace)
    assert not path.exists(), (
        f"{path} survived a confirmed teardown; a stale pointer teaches a reader to "
        "distrust the next one, which may be true"
    )
