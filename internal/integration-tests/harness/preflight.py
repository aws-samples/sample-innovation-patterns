"""Environment and account probes for the IPA integration-test harness.

The contract, and it is the whole point of this module:

*   **Every probe returns ``(ok: bool, detail: str)`` and never raises.** A probe
    that cannot reach its subject reports ``(False, <verbatim error text>)``. This
    is what lets two callers apply opposite policies to the same value: an
    interactive maintainer reads a negative outcome as an environment gap, and a
    pipeline reads it as a failure. Neither needs a ``try``.
*   **The detail carries the underlying error verbatim, never a paraphrase.**
    ``iam:CreateRole`` can be denied by a service control policy, by a permission
    boundary, or by the named-IAM capability specifically, and the three read
    almost identically once summarised.
*   **No pytest import, and no side effects at import time.** ``conftest.py``
    imports this module in a later phase, and ``import preflight`` must create no
    AWS resource and run no probe.

Two of the nine probes exist to retire unknowns that could make the whole harness
impossible, and both cost cents rather than a billable run:

*   ``probe_iam_create_role`` — whether a two-role stack with explicit role names
    deploys under ``CAPABILITY_NAMED_IAM``.
*   ``probe_cognito_token`` — whether a user pool with
    ``AdvancedSecurityMode: ENFORCED`` (``infra/cfn/cognito/cognito.yml``) still
    answers a programmatic ``InitiateAuth`` with tokens. The natural fallback is
    unavailable: ``ALLOW_ADMIN_USER_PASSWORD_AUTH`` is absent from the pool
    client's ``ExplicitAuthFlows``, so ``AdminInitiateAuth`` would need a change
    to a customer-facing template.

Run it directly::

    python -m preflight
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import string
import subprocess  # nosec B404 - argv lists only, shell=False; see .ash/ash.yaml
import sys
from pathlib import Path

from botocore.exceptions import BotoCoreError, ClientError

from harness import aws

# --------------------------------------------------------------------------- #
# Configuration. Every value is overridable from the environment so Phase 5's
# CI seam has somewhere to attach without editing this file.
#
# There is deliberately NO profile constant here. Credentials come from the
# default chain via ``harness.aws.session`` -- see ``_session`` below.
# --------------------------------------------------------------------------- #

REGION = aws.REGION

PROBE_NAMESPACE = "itprobe"
PROBE_ENV = "dev"

WORKER_MODEL_ID = os.environ.get(
    "IPA_IT_WORKER_MODEL", "anthropic.claude-3-haiku-20240307-v1:0"
)
DRIVER_MODEL_ID = os.environ.get(
    "IPA_IT_DRIVER_MODEL", "us.anthropic.claude-sonnet-4-20250514-v1:0"
)

# HITL default K1.A: ReadOnlyAccess, not PowerUserAccess.
#
# /ipa-deploy Step 1.5 checks only that {ns}-{env}-security reports
# CREATE_COMPLETE or UPDATE_COMPLETE; it never assumes either role, and
# APP_BUILDER_ROLE_ARN appears zero times in MAKEFILE_TEMPLATES.md. So
# ReadOnlyAccess satisfies that gate identically with a strictly smaller IAM
# footprint, and it removes the tension with .context/README.md's "no wildcard
# IAM resource ARNs" constraint that PowerUserAccess would introduce.
PROBE_MANAGED_POLICY_ARN = "arn:aws:iam::aws:policy/ReadOnlyAccess"

# Repository root, resolved from this file rather than from the caller's cwd.
#
# ``parents[3]``, not ``parents[2]``: this module moved down one level into
# ``harness/``, so the hop count grew by one -- ``harness/`` ->
# ``integration-tests/`` -> ``internal/`` -> repo root. At ``parents[2]`` the Cognito
# template below resolves to ``internal/infra/cfn/...``, which does not exist, and the
# blocking check fails on a missing file rather than on anything about the account.
REPO_ROOT = Path(__file__).resolve().parents[3]
COGNITO_TEMPLATE = REPO_ROOT / "infra" / "cfn" / "cognito" / "cognito.yml"

_IAM_STACK = f"{PROBE_NAMESPACE}-{PROBE_ENV}-security"
_COGNITO_STACK = f"{PROBE_NAMESPACE}-{PROBE_ENV}-cognito"

# Mirrors /ipa-security's generated iam.yml (SKILL.md:296-341) structurally:
# two roles with EXPLICIT RoleNames -- which is what forces
# CAPABILITY_NAMED_IAM -- one trusting the account root and one trusting
# codebuild.amazonaws.com, each attaching a single managed-policy ARN passed as
# a parameter.
#
# Structural fidelity is the point. A probe that created one unnamed role would
# succeed in an account that denies exactly what /ipa-security needs.
#
# Written at probe time rather than committed as a template file: a committed
# copy would be a second definition of /ipa-security's role shape, and it would
# drift silently.
_IAM_PROBE_TEMPLATE = """\
AWSTemplateFormatVersion: '2010-09-09'
Description: 'IPA integration-test preflight probe -- mirrors /ipa-security iam.yml'

Parameters:
  Namespace:
    Type: String
  Environment:
    Type: String
  AccountId:
    Type: String
  ManagedPolicyArn:
    Type: String

Resources:
  BuilderExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub "${Namespace}-${Environment}-builder"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub "arn:aws:iam::${AccountId}:root"
            Action: "sts:AssumeRole"
      ManagedPolicyArns:
        - !Ref ManagedPolicyArn

  CodeBuildExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub "${Namespace}-${Environment}-codebuild"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: "sts:AssumeRole"
      ManagedPolicyArns:
        - !Ref ManagedPolicyArn

Outputs:
  BuilderRoleArn:
    Value: !GetAtt BuilderExecutionRole.Arn
  CodeBuildRoleArn:
    Value: !GetAtt CodeBuildExecutionRole.Arn
"""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _session():
    """One session, passed to every AWS probe. Region PINNED, credentials AMBIENT.

    The region is explicit because this shell exports ``AWS_REGION=us-west-2``, and an
    inherited region would silently probe the wrong account and report it clean --
    clean because nothing was ever there, which is indistinguishable from a pass.

    The credentials are ambient BY DESIGN, which is the opposite of what this docstring
    used to argue. The default chain reads the environment or an SSO cache on a
    workstation and the ECS container role inside CodeBuild, so one code path serves
    both and no maintainer's profile name appears in source. The region argument was
    never the reason to name a profile; only the region needed pinning.
    """
    return aws.session(REGION)


def _run(argv: list[str], timeout: int = 30) -> tuple[bool, str]:
    """Run ``argv`` with ``shell=False`` and fold every failure into a pair.

    An argv list means no shell quoting applies, so paths containing spaces pass
    through intact -- which is what makes the B603 suppression in
    ``.ash/ash.yaml`` true rather than merely written.
    """
    try:
        proc = subprocess.run(  # nosec B603 B607 - argv list, shell=False
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return False, f"{argv[0]}: not found on PATH"
    except subprocess.TimeoutExpired:
        return False, f"{argv[0]}: timed out after {timeout}s"
    except OSError as exc:  # pragma: no cover - defensive
        return False, f"{argv[0]}: {exc}"
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        return False, f"exit {proc.returncode}: {detail}"
    return True, (proc.stdout or "").strip()


def _aws_error(exc: Exception) -> str:
    """Render an AWS exception with its verbatim message, never a paraphrase."""
    if isinstance(exc, ClientError):
        err = exc.response.get("Error", {})
        return f"{err.get('Code', 'ClientError')}: {err.get('Message', str(exc))}"
    if isinstance(exc, BotoCoreError):
        return f"{type(exc).__name__}: {exc}"
    return f"{type(exc).__name__}: {exc}"


def _stack_failure_reasons(cfn, stack_name: str) -> str:
    """Read a stack's failure events and return their reasons verbatim.

    This is the single most expensive thing to lose in this module: a service
    control policy denial, a permission boundary denial, and a named-IAM
    capability denial read almost identically once summarised.
    """
    try:
        events = cfn.describe_stack_events(StackName=stack_name)["StackEvents"]
    except Exception as exc:  # noqa: BLE001 - diagnostics must not raise
        return f"(could not read stack events: {_aws_error(exc)})"
    reasons = [
        f"{e.get('LogicalResourceId')}: {e['ResourceStatusReason']}"
        for e in events
        if e.get("ResourceStatusReason")
        and "FAILED" in str(e.get("ResourceStatus", ""))
    ]
    return " | ".join(reasons[:5]) if reasons else "(no failure reason recorded)"


def _delete_stack(cfn, stack_name: str) -> tuple[bool, str]:
    """Delete a stack and wait. Returns the standing stack name on timeout."""
    try:
        cfn.delete_stack(StackName=stack_name)
        cfn.get_waiter("stack_delete_complete").wait(
            StackName=stack_name,
            WaiterConfig={"Delay": 10, "MaxAttempts": 60},
        )
        return True, f"{stack_name} deleted"
    except Exception as exc:  # noqa: BLE001 - teardown must not raise
        return False, f"{stack_name} may still be standing: {_aws_error(exc)}"


def _generated_password(length: int = 20) -> str:
    """A password satisfying all four required character classes, by construction.

    ``cognito.yml``'s ``Policies.PasswordPolicy`` requires lowercase, uppercase,
    digits and symbols -- all four. Built by class rather than by rejection
    sampling, so it cannot fail intermittently.

    Held in memory only. Never written to any file.
    """
    symbols = "!@#$%^&*()-_=+"
    pools = [string.ascii_lowercase, string.ascii_uppercase, string.digits, symbols]
    chars = [secrets.choice(p) for p in pools]
    alphabet = "".join(pools)
    chars += [secrets.choice(alphabet) for _ in range(length - len(pools))]
    # Shuffle without Random(): secrets-driven Fisher-Yates.
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def _jwt_payload(token: str) -> dict:
    """Base64-decode a JWT's payload WITHOUT verifying its signature.

    Deliberately unverified, and narrowly so: this token was minted seconds
    earlier by this module against the pool it just deployed, and the only claim
    read is compared to a value from that same deployment. Verifying would add a
    JWKS fetch and a crypto dependency to establish something already known.

    Never a pattern for anything that trusts an inbound token.
    """
    segment = token.split(".")[1]
    segment += "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(segment))


def _domain_prefix(account_id: str) -> str:
    """``itprobe-dev-<short account hash>``.

    Deterministic per account so it is diagnosable, distinct across accounts so
    two accounts do not collide on a globally-unique name, and containing none of
    ``cognito``, ``aws`` or ``amazon`` -- which ``cognito.yml``'s own comment
    records that Cognito rejects.
    """
    digest = hashlib.sha256(account_id.encode()).hexdigest()[:8]
    return f"{PROBE_NAMESPACE}-{PROBE_ENV}-{digest}"


# --------------------------------------------------------------------------- #
# Cheap probes -- binaries and imports, no AWS call
# --------------------------------------------------------------------------- #


def probe_credentials_resolvable() -> tuple[bool, str]:
    """The default credential chain yields credentials, and WHICH LINK answered.

    Reporting only that credentials resolved would hide the interesting failure. The
    two environments this harness runs in resolve by different links -- ``env`` or
    ``sso`` on a workstation, ``container-role`` in CodeBuild -- and the case worth
    catching is resolving via the wrong one: a CI build answering from a long-lived
    environment key instead of its task role has resolved credentials successfully and
    is still misconfigured. Naming the link is what makes that visible in the row.
    """
    try:
        creds = _session().get_credentials()
    except Exception as exc:  # noqa: BLE001
        return False, f"credential chain: {_aws_error(exc)}"
    if creds is None:
        return False, "credential chain yielded no credentials"
    return True, f"resolved by {creds.method!r} in {REGION}"


def probe_sts_caller_identity() -> tuple[bool, str]:
    """``sts:GetCallerIdentity`` succeeds.

    Reports the account id and caller ARN, because those are the two facts
    ``DECISIONS.md`` is required to name.
    """
    try:
        ident = _session().client("sts").get_caller_identity()
    except Exception as exc:  # noqa: BLE001
        return False, _aws_error(exc)
    return True, f"account={ident['Account']} arn={ident['Arn']}"


def probe_claude_agent_sdk_importable() -> tuple[bool, str]:
    """``import claude_agent_sdk`` succeeds.

    A negative outcome is expected before Phase 2 declares the optional extra,
    and reads as a missing optional dependency rather than a failure of this
    module.
    """
    try:
        import claude_agent_sdk  # noqa: PLC0415
    except ImportError as exc:
        return False, f"optional dependency not installed: {exc}"
    version = getattr(claude_agent_sdk, "__version__", "unknown version")
    return True, f"claude_agent_sdk {version}"


def probe_docker_daemon() -> tuple[bool, str]:
    """The Docker daemon is answering.

    Reads a SERVER-only field. Deliberately NOT an exit-code check: ``docker
    info`` exits 0 with a partial payload when the daemon is down -- the client
    half of the output is still valid -- so an exit-code check reports a working
    daemon that is not there, and the failure resurfaces twenty minutes later
    inside ``build-rest-lambda``.

    Empty output is treated as a stopped daemon, which is the safe direction: a
    future format change yields a false negative (a skip), never a false positive
    that costs a container build.
    """
    ok, out = _run(["docker", "info", "--format", "{{.ServerVersion}}"])
    if not ok:
        return False, f"daemon not responding: {out}"
    if not out.strip():
        return False, "daemon not responding: docker info returned no ServerVersion"
    return True, f"docker server {out.strip()}"


def probe_npm_present() -> tuple[bool, str]:
    """``npm`` is on PATH. Reports the resolved version, not merely presence."""
    ok, out = _run(["npm", "--version"])
    return (True, f"npm {out}") if ok else (False, out)


def probe_uv_present() -> tuple[bool, str]:
    """``uv`` is on PATH. Reports the resolved version, not merely presence."""
    ok, out = _run(["uv", "--version"])
    return (True, out) if ok else (False, out)


def _probe_bedrock(model_id: str, label: str) -> tuple[bool, str]:
    """Prove invoke access to ``model_id``.

    Reports access-denied distinctly from model-not-found, because the remedies
    differ: one is an IAM or model-access-request problem, the other is a wrong
    model id or a region without that model.
    """
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "."}],
        }
    )
    try:
        _session().client("bedrock-runtime").invoke_model(
            modelId=model_id, body=body, contentType="application/json"
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        message = exc.response.get("Error", {}).get("Message", str(exc))
        if code in ("AccessDeniedException", "UnauthorizedOperation"):
            return False, f"{label}: ACCESS DENIED -- {message}"
        if code in ("ResourceNotFoundException", "ValidationException"):
            return False, f"{label}: MODEL NOT FOUND/INVALID -- {message}"
        return False, f"{label}: {code}: {message}"
    except Exception as exc:  # noqa: BLE001
        return False, f"{label}: {_aws_error(exc)}"
    return True, f"{label}: invoke ok ({model_id})"


def probe_bedrock_worker_model() -> tuple[bool, str]:
    """Invoke access to the model the queue worker uses."""
    return _probe_bedrock(WORKER_MODEL_ID, "worker model")


def probe_bedrock_driver_model() -> tuple[bool, str]:
    """Invoke access to the model the driver session itself runs on."""
    return _probe_bedrock(DRIVER_MODEL_ID, "driver model")


# --------------------------------------------------------------------------- #
# Blocking probe 1: named IAM role creation
# --------------------------------------------------------------------------- #


def probe_iam_create_role() -> tuple[bool, str]:
    """Deploy and delete a two-role stack mirroring /ipa-security's iam.yml.

    Reading a policy document cannot establish this. The account may deny
    ``iam:CreateRole``, or deny ``CAPABILITY_NAMED_IAM`` specifically, and either
    failure makes the whole harness impossible.
    """
    session = _session()
    cfn = session.client("cloudformation")
    try:
        account_id = session.client("sts").get_caller_identity()["Account"]
    except Exception as exc:  # noqa: BLE001
        return False, f"could not resolve account id: {_aws_error(exc)}"

    created = False
    try:
        cfn.create_stack(
            StackName=_IAM_STACK,
            TemplateBody=_IAM_PROBE_TEMPLATE,
            Parameters=[
                {"ParameterKey": "Namespace", "ParameterValue": PROBE_NAMESPACE},
                {"ParameterKey": "Environment", "ParameterValue": PROBE_ENV},
                {"ParameterKey": "AccountId", "ParameterValue": account_id},
                {
                    "ParameterKey": "ManagedPolicyArn",
                    "ParameterValue": PROBE_MANAGED_POLICY_ARN,
                },
            ],
            # Explicit RoleNames are what force this capability, so the probe
            # must pass it -- otherwise it tests a different thing than
            # /ipa-security does.
            Capabilities=["CAPABILITY_NAMED_IAM"],
        )
        created = True
        cfn.get_waiter("stack_create_complete").wait(
            StackName=_IAM_STACK,
            WaiterConfig={"Delay": 10, "MaxAttempts": 60},
        )
    except Exception as exc:  # noqa: BLE001
        reasons = _stack_failure_reasons(cfn, _IAM_STACK) if created else ""
        detail = f"{_aws_error(exc)}"
        if reasons:
            detail = f"{detail} || CFN: {reasons}"
        return False, detail
    finally:
        # Unconditional teardown, so a probe that fails midway still cleans up.
        if created:
            _delete_stack(cfn, _IAM_STACK)

    return True, (
        f"two named roles created and deleted under {PROBE_NAMESPACE} "
        f"with {PROBE_MANAGED_POLICY_ARN.rsplit('/', 1)[-1]} "
        f"and CAPABILITY_NAMED_IAM"
    )


# --------------------------------------------------------------------------- #
# Blocking probe 2: a programmatic Cognito identity token
# --------------------------------------------------------------------------- #


def probe_cognito_token() -> tuple[bool, str]:
    """Deploy the project's own Cognito template and mint an IdToken from it.

    Deploying ``infra/cfn/cognito/cognito.yml`` unchanged is the only way to test
    the property in question: ``AdvancedSecurityMode: ENFORCED`` is a property of
    THAT template, and a hand-written pool without it would pass while proving
    nothing.

    There is no fallback. ``ALLOW_ADMIN_USER_PASSWORD_AUTH`` is absent from the
    pool client's ``ExplicitAuthFlows``, so ``AdminInitiateAuth`` would require a
    change to a customer-facing deliverable.
    """
    if not COGNITO_TEMPLATE.is_file():
        return False, f"template not found: {COGNITO_TEMPLATE}"

    session = _session()
    cfn = session.client("cloudformation")
    idp = session.client("cognito-idp")

    try:
        account_id = session.client("sts").get_caller_identity()["Account"]
    except Exception as exc:  # noqa: BLE001
        return False, f"could not resolve account id: {_aws_error(exc)}"

    prefix = _domain_prefix(account_id)
    created = False
    notes: list[str] = []

    try:
        cfn.create_stack(
            StackName=_COGNITO_STACK,
            TemplateBody=COGNITO_TEMPLATE.read_text(),
            Parameters=[
                {"ParameterKey": "Namespace", "ParameterValue": PROBE_NAMESPACE},
                {"ParameterKey": "Environment", "ParameterValue": PROBE_ENV},
                {"ParameterKey": "CognitoDomainPrefix", "ParameterValue": prefix},
                # DeletionProtection left at its INACTIVE default on purpose:
                # passing ACTIVE would strand this stack.
            ],
            Capabilities=["CAPABILITY_IAM"],
        )
        created = True
        cfn.get_waiter("stack_create_complete").wait(
            StackName=_COGNITO_STACK,
            WaiterConfig={"Delay": 10, "MaxAttempts": 90},
        )

        outputs = {
            o["OutputKey"]: o["OutputValue"]
            for o in cfn.describe_stacks(StackName=_COGNITO_STACK)["Stacks"][0].get(
                "Outputs", []
            )
        }
        pool_id = outputs.get("UserPoolId")
        client_id = outputs.get("UserPoolClientId")
        if not pool_id or not client_id:
            return False, f"stack outputs missing UserPoolId/UserPoolClientId: {outputs}"

        username = f"itprobe-{secrets.token_hex(4)}@example.invalid"
        password = _generated_password()  # in memory only; never written anywhere

        idp.admin_create_user(
            UserPoolId=pool_id,
            Username=username,
            # No mail to a non-existent address.
            MessageAction="SUPPRESS",
            UserAttributes=[
                {"Name": "email", "Value": username},
                {"Name": "email_verified", "Value": "true"},
            ],
        )
        # Permanent=True clears FORCE_CHANGE_PASSWORD, which would otherwise
        # answer InitiateAuth with a NEW_PASSWORD_REQUIRED challenge.
        idp.admin_set_user_password(
            UserPoolId=pool_id, Username=username, Password=password, Permanent=True
        )

        auth = idp.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )

        if "ChallengeName" in auth:
            # Recorded verbatim: adaptive authentication challenging this call is
            # the finding that would block the whole feature.
            return False, (
                f"adaptive auth challenged InitiateAuth -- "
                f"ChallengeName={auth['ChallengeName']!r} "
                f"ChallengeParameters={auth.get('ChallengeParameters')!r}"
            )

        id_token = auth.get("AuthenticationResult", {}).get("IdToken")
        if not id_token:
            return False, f"no IdToken in AuthenticationResult: {auth.get('AuthenticationResult', {}).keys()}"

        # The ID token, not the access token: only the ID token carries
        # aud = client_id, which is what the API Gateway authorizer checks later.
        aud = _jwt_payload(id_token).get("aud")
        if aud != client_id:
            return False, f"IdToken aud={aud!r} != UserPoolClientId={client_id!r}"
        notes.append(f"IdToken aud == UserPoolClientId ({client_id})")

    except Exception as exc:  # noqa: BLE001
        reasons = _stack_failure_reasons(cfn, _COGNITO_STACK) if created else ""
        detail = _aws_error(exc)
        if reasons:
            detail = f"{detail} || CFN: {reasons}"
        return False, detail
    finally:
        if created:
            ok_del, del_detail = _delete_stack(cfn, _COGNITO_STACK)
            notes.append(del_detail)
            if ok_del:
                # A leaked domain prefix is globally unique, so a leak makes this
                # probe non-repeatable with an error that names a name rather
                # than a cause.
                try:
                    dom = idp.describe_user_pool_domain(Domain=prefix)
                    released = not dom.get("DomainDescription", {}).get("UserPoolId")
                except Exception:  # noqa: BLE001
                    released = True
                notes.append(
                    f"domain prefix {prefix} released"
                    if released
                    else f"domain prefix {prefix} STILL CLAIMED"
                )

    return True, "; ".join(notes)


# --------------------------------------------------------------------------- #
# The ordered probe table and the runner
# --------------------------------------------------------------------------- #

# The NINE prerequisites, cheapest-first: binaries and imports before any AWS
# call, and the stack-deploying probe last. A machine with no credentials gets
# its answer in milliseconds, and strict mode (Phase 5) fails fast for free.
#
# ``cognito_token`` is deliberately NOT in this table. It is not a prerequisite
# any later test skips on -- it is a one-off blocking check that answers "can
# this feature exist at all", and it deploys a user pool to do so. Keeping it out
# means ``conftest.py`` cannot accidentally deploy a pool while deciding whether
# to skip a test. It is run explicitly by ``main()`` and is reachable through
# ``run_probe`` by name.
PROBES: tuple[tuple[str, object], ...] = (
    ("credentials_resolvable", probe_credentials_resolvable),
    ("sts_caller_identity", probe_sts_caller_identity),
    ("claude_agent_sdk_importable", probe_claude_agent_sdk_importable),
    ("npm_present", probe_npm_present),
    ("uv_present", probe_uv_present),
    ("docker_daemon", probe_docker_daemon),
    ("bedrock_worker_model", probe_bedrock_worker_model),
    ("bedrock_driver_model", probe_bedrock_driver_model),
    ("iam_create_role", probe_iam_create_role),
)

BLOCKING_CHECKS: tuple[tuple[str, object], ...] = (
    ("cognito_token", probe_cognito_token),
)


def run_probe(name: str) -> tuple[bool, str]:
    """Run one probe by name. Used by ``conftest.py``'s single ``_unmet`` helper."""
    for probe_name, fn in PROBES + BLOCKING_CHECKS:
        if probe_name == name:
            return fn()  # type: ignore[operator]
    return False, f"unknown probe {name!r}"


def main(include_blocking: bool = True) -> int:
    """Run every probe and print one row each.

    Deliberately does NOT short-circuit on the first negative outcome: that would
    hide a second unmet prerequisite behind the first, turning one round of
    environment repair into several -- and nothing is saved by stopping, because
    the expensive probes are last.
    """
    print(f"IPA integration-test preflight -- region={REGION}\n")
    results: list[tuple[str, bool, str]] = []

    for name, fn in PROBES:
        ok, detail = fn()  # type: ignore[operator]
        results.append((name, ok, detail))
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<30}  {detail}")

    if include_blocking:
        print("\n  -- blocking check (deploys and deletes a Cognito user pool) --")
        for name, fn in BLOCKING_CHECKS:
            ok, detail = fn()  # type: ignore[operator]
            results.append((name, ok, detail))
            print(f"  {'PASS' if ok else 'FAIL'}  {name:<30}  {detail}")

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print(f"unmet: {', '.join(failed)}")
    # Non-zero on any negative outcome, so the command is scriptable -- while
    # still having printed every row.
    return 1 if failed else 0


if __name__ == "__main__":
    # --probes-only skips the blocking Cognito check, so the nine-row table can
    # be printed without deploying anything.
    sys.exit(main(include_blocking="--probes-only" not in sys.argv))
