"""Composition assertions, made against a run that stopped at ``/ipa-compose``.

Each assertion is here because its absence is **silent**. Two of them pay for the
whole phase by catching, at composition price, a defect that would otherwise surface
twenty minutes into a build or not at all:

*   ``cd web-client`` in ``build.mk`` — the template may emit ``cd frontend``, which
    does not exist in this repository.
*   ``update-env-backend`` / ``update-env-frontend`` in ``env.mk`` — their absence is
    fully silent: the deployment succeeds and the frontend is served a config naming
    no API and no identity provider, failing in the browser with nothing in any
    deployment log.

A failure here is recorded in ``DECISIONS.md`` with its line cite and **blocks
Phase 4**, because ``.claude/skills/**`` and ``MAKEFILE_TEMPLATES.md`` are public
interface and each fix is its own change with a bumping commit type.
"""

from __future__ import annotations

import pytest

import artifacts
import standing

pytestmark = pytest.mark.integration


EXPECTED_TIERS = {"frontend", "backend", "queue"}
EXPECTED_PREPARE_TARGETS = ("prepare-logs", "prepare-ecr", "prepare-cognito")


@pytest.fixture(scope="module")
def project(compose_run, temp_project):
    """The composed temp project. Depends on ``compose_run`` so the drive happens."""
    return temp_project.root


@pytest.fixture(scope="module")
def deploy_mk(project) -> str:
    return artifacts.read(project, "scripts/deploy.mk")


# --------------------------------------------------------------------------- #
# The run reached compose and stopped
# --------------------------------------------------------------------------- #


def test_the_run_reached_the_compose_completion_report(compose_run, project):
    """The economic argument for this phase is that composition creates no billable
    resources beyond two free IAM roles."""
    assert not compose_run.stopped_by_ceiling, (
        f"a ceiling stopped the run rather than the agent finishing: "
        f"cost=${compose_run.cost_usd} turns={compose_run.turns}"
    )
    assert (project / "scripts" / "deploy.mk").is_file(), (
        "compose did not reach artifact generation; see the transcript's verbatim "
        "gate text for where it stopped"
    )


def test_the_run_stopped_before_prepare(project):
    """No prepare or deploy step ran.

    Their side effects are what this asserts on, not the absence of a log line: a
    deployed stack under the namespace other than security would mean the stop
    instruction was not honoured.
    """
    # Asserted against AWS in test_no_unexpected_stacks_exist below; here we check
    # the local evidence that no deployment was attempted.
    assert not (project / ".ipa-deployed").exists()


def test_the_answer_channel_is_recorded(compose_run):
    """Which path delivered each batch, so an SDK channel switch appears as a channel
    change rather than as a wrong namespace three steps later."""
    assert compose_run.channels_used, "no question batch was recorded as answered"
    assert compose_run.channels_used <= {"pre_tool_use_hook", "can_use_tool"}


# --------------------------------------------------------------------------- #
# THE discriminator
# --------------------------------------------------------------------------- #


def test_env_namespace_equals_the_generated_namespace(project, namespace):
    """The ONLY discriminator between "the harness answered" and "the agent used
    skill defaults".

    ``AWS_REGION=us-east-1``, ``APP_ENV=dev`` and ``APP_IAC=cloudformation`` are each
    themselves ``/ipa-init``'s recommended option, so agreement on any of them is
    consistent with **no answer having been delivered at all**. Pinning ``us-east-1``
    was chosen deliberately to keep that property intact, which makes this assertion
    the one that carries it.
    """
    env_file = project / ".env"
    assert env_file.is_file(), "/ipa-init did not write .env"
    values = standing.parse_env(env_file)

    assert values.get("APP_NAMESPACE") == namespace, (
        f"APP_NAMESPACE is {values.get('APP_NAMESPACE')!r}, expected {namespace!r}. "
        "If it is 'app', the skill's default won and the answers never reached it."
    )


def test_env_carries_a_real_aws_profile(project, aws_profile):
    """'Skip' is the RECOMMENDED option for AWS_PROFILE and omits the line entirely,
    while three downstream skills require it."""
    values = standing.parse_env(project / ".env")
    assert values.get("AWS_PROFILE") == aws_profile


def test_env_pins_the_region_and_engine(project):
    values = standing.parse_env(project / ".env")
    assert values.get("AWS_REGION") == "us-east-1"
    assert values.get("APP_ENV") == "dev"
    assert values.get("APP_IAC") == "cloudformation"


# --------------------------------------------------------------------------- #
# All eight artifacts
# --------------------------------------------------------------------------- #


def test_all_eight_artifacts_exist(project):
    """The claim that all eight are generated is the skill's own
    (``ipa-compose/SKILL.md:266-274``) and had never been observed on a real run."""
    missing = artifacts.missing_artifacts(project)
    assert missing == [], f"/ipa-compose did not generate: {missing}"


# --------------------------------------------------------------------------- #
# The composed architecture
# --------------------------------------------------------------------------- #


def test_deploy_mk_header_tier_set(deploy_mk):
    tiers = artifacts.header_tiers(deploy_mk)
    assert tiers == EXPECTED_TIERS, (
        f"composed tiers are {sorted(tiers)}, expected {sorted(EXPECTED_TIERS)}; a "
        "composition that omits a tier generates artifacts that succeed at "
        "everything they attempt while deploying a different architecture"
    )


@pytest.mark.parametrize("target", EXPECTED_PREPARE_TARGETS)
def test_prepare_mk_declares_each_auto_included_tier(project, target):
    text = artifacts.read(project, "scripts/prepare.mk")
    assert target in artifacts.targets(text), (
        f"{target} missing; the auto-include resolver did not add its tier"
    )


def test_deploy_backend_enables_the_sqs_integration(deploy_mk):
    """The ONLY artifact-level proof that Step 3.4's cross-tier auto-wiring fired.

    Without it the tiers deploy independently and the failure appears only at
    runtime, as a job accepted and never processed.
    """
    params = artifacts.parameter_overrides(deploy_mk, "deploy-backend")
    assert params.get("EnableSqsIntegration") == "true", (
        f"deploy-backend parameter overrides are {params}; EnableSqsIntegration=true "
        "is absent, so the queue was composed but never wired to the backend"
    )


def test_teardown_is_the_exact_reverse_of_deploy(deploy_mk):
    """Compares tier SUFFIXES: ``MAKEFILE_TEMPLATES.md:54`` generates ``deploy-{s}``
    and ``:162`` generates ``teardown-{s}``, so the two lists never share a name."""
    ok, dep, tear = artifacts.teardown_is_reverse_of_deploy(deploy_mk)
    assert ok, f"deploy: {dep}\nteardown: {tear}\nteardown must be the exact reverse"


# --------------------------------------------------------------------------- #
# The two costly defects
# --------------------------------------------------------------------------- #


def test_build_mk_references_web_client_not_frontend(project):
    """Defect 4. ``cd frontend`` does not exist in this repository, and undetected it
    fails twenty minutes into a build with an error about a missing directory."""
    text = artifacts.read(project, "scripts/build.mk")
    assert "cd frontend" not in text, (
        "build.mk emits `cd frontend`, which does not exist here; the frontend tree "
        "is web-client/"
    )
    assert "web-client" in text, "build.mk does not reference web-client/ at all"


def test_build_mk_declares_exactly_one_container_build_target(project):
    text = artifacts.read(project, "scripts/build.mk")
    count = artifacts.target_count(text, "build-rest-lambda")
    assert count == 1, (
        f"build-rest-lambda is declared {count} times; a duplicate either builds "
        "twice or builds the wrong one depending on ordering"
    )


@pytest.mark.parametrize("target", ["update-env-backend", "update-env-frontend"])
def test_env_mk_declares_both_sync_targets(project, target):
    """Defect 5. Absence is fully silent: the deployment succeeds and the frontend is
    served a config naming no API and no identity provider, failing in the browser
    with nothing in any deployment log."""
    text = artifacts.read(project, "scripts/env.mk")
    assert target in artifacts.targets(text), f"env.mk does not declare {target}"


# --------------------------------------------------------------------------- #
# The account
# --------------------------------------------------------------------------- #


def test_no_unexpected_stacks_exist(namespace, aws_profile):
    """Only ``{ns}-{env}-security`` may exist. Route A deploys it -- two named IAM
    roles, free but real -- so this phase is NOT strictly zero-AWS."""
    stacks, error = standing.live_stacks(namespace, aws_profile, "us-east-1")
    assert not error, f"could not list stacks: {error}"

    unexpected = [n for n, _ in stacks if not n.endswith("-security")]
    assert unexpected == [], (
        f"the stop-after-compose instruction was not honoured; these stacks were "
        f"deployed: {unexpected}"
    )
