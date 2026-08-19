"""Live assertions against a completed IPA deployment.

These assert the **architecture**, not the run. A run that completed `/ipa-deploy`
without error has established that the Makefiles ran — not that a user can load the
application, that the API refuses an anonymous caller, that a real token is accepted,
or that a submitted job reaches a worker.

Three assertions carry stated limits, and each limit is in the test's own docstring
so a later reader cannot over-read the assertion:

*   The 401 check **cannot** establish that the container runs.
*   The container probe is what establishes that, and needs three conditions.
*   The job check stops at "left `PENDING`", and **a `FAILED` job passes**.
"""

from __future__ import annotations

import json
import time

import pytest
import requests

from harness import aws, cognito_auth, standing

pytestmark = pytest.mark.integration

# Both from ``harness.standing``, never restated here. ``deploy/conftest.py``'s
# completion gate reads the same tuple, and a second copy would let the gate that
# decides "the lifecycle finished" disagree with the assertions that check what it
# produced -- silently, in both directions.
HEALTHY = standing.HEALTHY_STATES
EXPECTED_TIERS = standing.EXPECTED_TIERS

JOB_POLL_TIMEOUT_S = 120
JOB_POLL_INTERVAL_S = 5
HTTP_TIMEOUT_S = 30


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def session():
    """Region pinned, credentials from the default chain -- one policy, in harness.aws."""
    return aws.session()


@pytest.fixture(scope="module")
def cfn(session):
    return session.client("cloudformation")


def _outputs(cfn, stack_name: str) -> dict[str, str]:
    stack = cfn.describe_stacks(StackName=stack_name)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}


@pytest.fixture(scope="module")
def stacks(deploy_run, namespace):
    found, error = standing.live_stacks(namespace, aws.REGION)
    assert not error, f"could not list stacks: {error}"
    return dict(found)


@pytest.fixture(scope="module")
def app_url(cfn, namespace) -> str:
    """From CloudFormation OUTPUTS, never from ``.env``.

    ``.env`` is populated by ``env.mk``'s ``update-env-*`` targets, so reading from it
    makes one missing target fail every downstream probe with a blank URL — destroying
    the diagnostic value of every assertion after it instead of failing the one check
    that owns it.
    """
    out = _outputs(cfn, f"{namespace}-dev-frontend")
    url = out.get("DistributionUrl") or out.get("AppUrl") or out.get("CloudFrontUrl")
    assert url, f"frontend stack outputs carry no app URL: {sorted(out)}"
    return url.rstrip("/")


@pytest.fixture(scope="module")
def api_url(cfn, namespace) -> str:
    out = _outputs(cfn, f"{namespace}-dev-backend")
    url = out.get("ApiUrl") or out.get("ApiEndpoint") or out.get("HttpApiUrl")
    assert url, f"backend stack outputs carry no API URL: {sorted(out)}"
    return url.rstrip("/")


@pytest.fixture(scope="module")
def cognito_outputs(cfn, namespace) -> dict[str, str]:
    return _outputs(cfn, f"{namespace}-dev-cognito")


@pytest.fixture(scope="module")
def identity(cognito_outputs, transcript) -> cognito_auth.Identity:
    """The one write these assertions make: a throwaway user in the run's own pool.

    The pool's own deletion removes it, with no separate cleanup obligation.
    """
    ident = cognito_auth.mint_token(
        user_pool_id=cognito_outputs["UserPoolId"],
        client_id=cognito_outputs["UserPoolClientId"],
        region=aws.REGION,
    )
    # Register BEFORE anything can write it. The filter is keyed on the live value at
    # the writer, not applied by care at each write site.
    transcript.register_secret(ident.password)
    return ident


@pytest.fixture(scope="module")
def auth_headers(identity) -> dict[str, str]:
    return {"Authorization": f"Bearer {identity.id_token}"}


def _get_with_transient_retries(url: str, **kwargs) -> requests.Response:
    """GET, retrying ONLY on transport failures and 5xx.

    The Lambda Web Adapter — the shim fronting the container's web server — briefly
    serves 5xx while that server starts, so a 5xx is genuinely transient. A 401 or 403
    is a decision the gateway has already made: retrying it six times at ten-second
    intervals spends the whole startup window re-learning the same answer and then
    reports a timeout instead of the real result.
    """
    last: Exception | None = None
    for attempt in range(6):
        try:
            response = requests.get(url, timeout=HTTP_TIMEOUT_S, **kwargs)
        except requests.RequestException as exc:
            last = exc
            time.sleep(10)
            continue
        if response.status_code >= 500:
            time.sleep(10)
            continue
        return response
    raise AssertionError(f"no usable response from {url} after 6 attempts: {last}")


# --------------------------------------------------------------------------- #
# How the run got here
# --------------------------------------------------------------------------- #


def test_the_answer_channel_is_recorded(deploy_run):
    """Which path delivered each question batch.

    Deliberately NOT part of ``conftest.py``'s completion gate. A deployment can be
    entirely correct while the harness's resolver was never consulted -- that is
    exactly what happened on 2026-08-18, when ``/ipa-init``'s five-question call was
    rejected by ``AskUserQuestion``'s input validation and the agent filled ``.env``
    in from the appended system prompt instead. Failing the gate on it would throw
    away a completed billable deployment over a fact about the harness; failing one
    assertion reports it and keeps the rest of the run's evidence.

    An empty set therefore means: the pinned answers in ``harness.answers`` did not
    apply to this run, and anything they encode -- the namespace excepted, which the
    system prompt also pins -- reflects the skills' own defaults.
    """
    assert deploy_run.channels_used, (
        "no question batch was recorded as answered, so the resolver never fired. "
        "Check the transcript for an AskUserQuestion InputValidationError: a call "
        "with more than 4 questions, or any question offering fewer than 2 options, "
        "is rejected before the hook can answer it."
    )
    assert deploy_run.channels_used <= {"pre_tool_use_hook", "can_use_tool"}


# --------------------------------------------------------------------------- #
# Stacks
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("tier", EXPECTED_TIERS)
def test_expected_stack_exists_and_is_healthy(stacks, namespace, tier):
    """Presence alone is insufficient.

    A ``ROLLBACK_COMPLETE`` stack exists, holds resources, costs money, and is not a
    working deployment. ``UPDATE_ROLLBACK_COMPLETE`` IS accepted: it denotes a stack
    that reverted to a previously working configuration and is serving it, where
    ``ROLLBACK_COMPLETE`` denotes a creation that never succeeded.
    """
    name = f"{namespace}-dev-{tier}"
    assert name in stacks, f"{name} was not deployed; found {sorted(stacks)}"
    assert stacks[name] in HEALTHY, (
        f"{name} is {stacks[name]}, which is not a healthy completed state"
    )


def test_exactly_seven_stacks_under_the_namespace(stacks, namespace):
    assert len(stacks) == 7, f"expected 7 stacks, found {len(stacks)}: {sorted(stacks)}"


# --------------------------------------------------------------------------- #
# The served application
# --------------------------------------------------------------------------- #


def test_the_spa_is_served_through_cloudfront(app_url):
    """A distribution serving a directory listing or an access-denied document also
    returns a response; only the content distinguishes those from a deployment."""
    response = _get_with_transient_retries(app_url)
    assert response.status_code == 200, f"{app_url} -> {response.status_code}"
    body = response.text.lower()
    assert "<html" in body, f"{app_url} returned no HTML markup: {response.text[:300]}"
    assert "<div id=\"root\"" in body or "<script" in body, (
        "response carries no SPA mount point or script tag"
    )


def test_config_js_carries_the_deployed_cognito_client_id(app_url, cognito_outputs):
    """Compared against the cognito stack's OUTPUT, not against ``.env``."""
    response = _get_with_transient_retries(f"{app_url}/config.js")
    assert response.status_code == 200, f"config.js -> {response.status_code}"
    client_id = cognito_outputs["UserPoolClientId"]
    assert client_id in response.text, (
        f"config.js does not carry the deployed client id {client_id}; "
        f"update-env-frontend may not have run. Body: {response.text[:400]}"
    )


# --------------------------------------------------------------------------- #
# Auth layer 1: the gateway refuses an anonymous caller
# --------------------------------------------------------------------------- #


def test_unauthenticated_health_is_exactly_401(api_url):
    """A 403 FAILS, a 5xx FAILS, and no response FAILS.

    A 403 means a token was presented and rejected, or a resource policy denied the
    call — real misconfigurations with different fixes, and neither is the property
    being asserted. Accepting "any non-2xx" would let a resource-policy denial, a
    missing authorizer and a correct authorizer all pass identically.

    **This check cannot establish that the container runs.** ``app-lib`` lists
    ``/health`` in ``PUBLIC_PATHS`` (``app_lib/common/auth.py:24``), so this 401 comes
    from API Gateway's JWT authorizer in FRONT of the Lambda — which answers
    identically whether the container is healthy, crash-looping, or was never pushed.
    That guarantee belongs to ``test_the_backend_container_runs``.
    """
    response = _get_with_transient_retries(f"{api_url}/health")
    assert response.status_code == 401, (
        f"expected exactly 401, got {response.status_code}. A 403 means a token was "
        f"presented and rejected or a resource policy denied the call -- a different "
        f"fault. Body: {response.text[:300]}"
    )


# --------------------------------------------------------------------------- #
# Auth layer 2: a real token is accepted
# --------------------------------------------------------------------------- #


def test_authenticated_health_returns_ok(api_url, auth_headers):
    """Uses the ID token, not the access token: only the ID token carries
    ``aud = client_id``, unambiguous under both auth layers."""
    response = _get_with_transient_retries(f"{api_url}/health", headers=auth_headers)
    assert response.status_code == 200, (
        f"{api_url}/health with a valid ID token -> {response.status_code}: "
        f"{response.text[:300]}"
    )
    assert response.json().get("status") == "ok", response.text[:300]


def test_authenticated_jobs_collection_is_reachable(api_url, auth_headers):
    response = _get_with_transient_retries(
        f"{api_url}/api/v1/jobs", headers=auth_headers
    )
    assert response.status_code == 200, (
        f"{api_url}/api/v1/jobs -> {response.status_code}: {response.text[:300]}"
    )


# --------------------------------------------------------------------------- #
# The container actually runs
# --------------------------------------------------------------------------- #


def test_the_backend_container_runs(session, cfn, namespace):
    """Requires ALL THREE of: no ``FunctionError``, payload ``statusCode`` 200, and
    body ``status`` ``"ok"``.

    Lambda returns invocation ``StatusCode`` 200 **even when the handler raised** —
    the raise is reported in ``FunctionError``, not in the status — so the status
    alone would pass for a container that exists and throws.

    **This probe, not the 401, is what proves the container runs.** It reaches the
    handler without a token precisely because ``app-lib`` treats ``/health`` as
    public; that looks like a gap in the probe and is in fact what makes it possible.
    """
    out = _outputs(cfn, f"{namespace}-dev-backend")
    function_name = (
        out.get("FunctionName")
        or out.get("RestLambdaFunctionName")
        or out.get("BackendFunctionName")
    )
    assert function_name, f"backend outputs carry no function name: {sorted(out)}"

    event = {
        "version": "2.0",
        "routeKey": "GET /health",
        "rawPath": "/health",
        "rawQueryString": "",
        "headers": {"host": "probe.invalid", "accept": "application/json"},
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/health",
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
            },
            "routeKey": "GET /health",
            "stage": "$default",
        },
        "isBase64Encoded": False,
    }

    response = session.client("lambda").invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(event).encode(),
    )

    assert "FunctionError" not in response, (
        f"handler raised: {response.get('FunctionError')} -- "
        f"{response['Payload'].read().decode()[:500]}"
    )
    payload = json.loads(response["Payload"].read().decode())
    assert payload.get("statusCode") == 200, f"handler returned {payload}"
    body = payload.get("body")
    parsed = json.loads(body) if isinstance(body, str) else body
    assert parsed.get("status") == "ok", f"handler body: {parsed}"


# --------------------------------------------------------------------------- #
# The queue round trip
# --------------------------------------------------------------------------- #


def test_a_submitted_job_leaves_pending(api_url, auth_headers):
    """Stops at "no longer ``PENDING``". **A ``FAILED`` job PASSES.**

    This does NOT verify the inference result. Reaching ``COMPLETED`` additionally
    requires Bedrock access to ``anthropic.claude-3-haiku-20240307-v1:0``, a loaded
    passenger dataset, and an IAM scope excluding cross-region inference profiles —
    three account-state dependencies this test does not control. Phase 1's preflight
    measured that the worker model is **not invocable in this account** (the provider
    has marked it Legacy), so requiring ``COMPLETED`` would make this suite red for a
    reason that is not a defect in IPA.

    The terminal status and any recorded error ARE reported. The DLQ assertion is what
    catches a crash-looping worker, which this check alone would pass.

    Expect ``FAILED`` with ``Passenger not found: 113803`` on a namespace whose passenger
    table was never loaded — the fresh-namespace default. ``process_job`` catches every
    exception, records it on the job and returns 200, so such a failure is invisible to
    the DLQ by design; the two checks are not redundant.
    """
    # The shape is the SHIPPED contract, not a convenient placeholder: ``JobCreate``
    # (job_dto.py) requires ``input_data`` and has no ``prompt`` field, so a body this
    # test invents is rejected by FastAPI with 422 before ``submit_job`` runs -- measured
    # 2026-08-19. ``ticket`` is what the worker reads (sqs_handler.py: input_data
    # ["ticket"]); whether that passenger is loaded changes the terminal status but not
    # this test, which asserts only that the status stops being PENDING.
    submit = requests.post(
        f"{api_url}/api/v1/jobs",
        headers={**auth_headers, "Content-Type": "application/json"},
        json={"job_type": "passenger_analysis", "input_data": {"ticket": "113803"}},
        timeout=HTTP_TIMEOUT_S,
    )
    assert submit.status_code == 202, (
        f"POST /api/v1/jobs -> {submit.status_code}: {submit.text[:400]}\n"
        "A 422 means this test's body no longer matches JobCreate in "
        "app-lib/src/app_lib/features/jobs/routes/job_dto.py -- fix the body, not the "
        "DTO, unless the API contract genuinely changed."
    )
    created = submit.json()
    job_id = created.get("job_id") or created.get("id")
    assert job_id, f"submission returned no job id: {created}"
    assert created.get("status") == "PENDING", f"submitted job status: {created}"

    deadline = time.monotonic() + JOB_POLL_TIMEOUT_S
    terminal = None
    while time.monotonic() < deadline:
        poll = requests.get(
            f"{api_url}/api/v1/jobs/{job_id}", headers=auth_headers,
            timeout=HTTP_TIMEOUT_S,
        )
        if poll.status_code == 200:
            body = poll.json()
            if body.get("status") != "PENDING":
                terminal = body
                break
        time.sleep(JOB_POLL_INTERVAL_S)

    assert terminal is not None, (
        f"job {job_id} was still PENDING after {JOB_POLL_TIMEOUT_S}s; the worker is "
        "not consuming the queue"
    )
    # REPORTED, not asserted on. A FAILED job passes.
    print(
        f"\njob {job_id} reached terminal status {terminal.get('status')!r}"
        + (f" error={terminal.get('error')!r}" if terminal.get("error") else "")
    )


def test_the_dead_letter_queue_is_empty(cfn, session, namespace):
    """A message here is the clearest sign the worker is crash-looping.

    ``MaxReceiveCount`` defaults to 3 (``queue.yml``), so a message in the DLQ took
    three failed receives — repeatable failure rather than one transient error. This
    is what makes the lenient job check above safe.
    """
    out = _outputs(cfn, f"{namespace}-dev-queue")
    dlq_url = out.get("DlqUrl")
    assert dlq_url, f"queue outputs carry no DlqUrl: {sorted(out)}"

    attrs = session.client("sqs").get_queue_attributes(
        QueueUrl=dlq_url,
        AttributeNames=["ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible"],
    )["Attributes"]
    visible = int(attrs.get("ApproximateNumberOfMessages", 0))
    in_flight = int(attrs.get("ApproximateNumberOfMessagesNotVisible", 0))
    assert visible + in_flight == 0, (
        f"DLQ holds {visible} visible and {in_flight} in-flight message(s); the "
        "worker failed the same message three times"
    )


@pytest.mark.parametrize(
    "key", ["QueueUrl", "QueueArn", "WorkerFunctionName", "DlqUrl", "JobsTableArn"]
)
def test_queue_stack_output_resolves(cfn, namespace, key):
    """An output that does not resolve breaks the cross-tier wiring silently."""
    out = _outputs(cfn, f"{namespace}-dev-queue")
    assert out.get(key), f"queue stack output {key} does not resolve; got {sorted(out)}"


def test_the_event_source_mapping_is_enabled(cfn, session, namespace):
    """A disabled mapping produces a deployment where submissions succeed and are
    never delivered — from the API's side, indistinguishable from a slow worker."""
    out = _outputs(cfn, f"{namespace}-dev-queue")
    mappings = session.client("lambda").list_event_source_mappings(
        FunctionName=out["WorkerFunctionName"]
    )["EventSourceMappings"]
    assert mappings, "the worker has no event source mapping"
    mapping = mappings[0]
    assert mapping["State"] == "Enabled", f"mapping state is {mapping['State']}"
    assert mapping["BatchSize"] == 1, f"batch size is {mapping['BatchSize']}"
