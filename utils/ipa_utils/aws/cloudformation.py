"""CloudFormation API wrapper.

Functions:
    create_or_update_stack()  — Idempotent stack deployment
    delete_stack()            — Stack deletion with polling
    get_stack_outputs()       — Retrieve stack output values
    get_stack_status()        — Check if stack exists and its state
    get_stack_events()        — Read recent stack events

All functions accept an optional boto3 session for credential/region control.

Used by: ipa_utils.cli.deploy (CLI layer)
Tested by: tests/test_deploy_cfn.py (moto mocking)
"""

import time
from pathlib import Path

import boto3
import click
from botocore.exceptions import ClientError

from ipa_utils.helpers.output import info

# Terminal states for CloudFormation stack operations
TERMINAL_STATES = {
    "CREATE_COMPLETE",
    "UPDATE_COMPLETE",
    "DELETE_COMPLETE",
    "CREATE_FAILED",
    "ROLLBACK_COMPLETE",
    "ROLLBACK_FAILED",
    "UPDATE_ROLLBACK_COMPLETE",
    "UPDATE_ROLLBACK_FAILED",
    "DELETE_FAILED",
    "IMPORT_COMPLETE",
    "IMPORT_ROLLBACK_COMPLETE",
    "IMPORT_ROLLBACK_FAILED",
}

SUCCESS_STATES = {
    "CREATE_COMPLETE",
    "UPDATE_COMPLETE",
    "IMPORT_COMPLETE",
}


def get_boto3_session(
    profile: str | None = None,
    region: str | None = None,
) -> boto3.Session:
    """Create boto3 session with optional profile and region override."""
    kwargs: dict[str, str] = {}
    if profile:
        kwargs["profile_name"] = profile
    if region:
        kwargs["region_name"] = region
    return boto3.Session(**kwargs)


def get_stack_status(session: boto3.Session, stack_name: str) -> str | None:
    """Return stack status string or None if stack does not exist."""
    client = session.client("cloudformation")
    try:
        response = client.describe_stacks(StackName=stack_name)
        stacks = response.get("Stacks", [])
        if not stacks:
            return None
        return stacks[0]["StackStatus"]
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        if "does not exist" in error_message:
            return None
        raise


def create_or_update_stack(
    session: boto3.Session,
    stack_name: str,
    template_path: Path,
    parameters: dict[str, str] | None = None,
    capabilities: list[str] | None = None,
    tags: dict[str, str] | None = None,
    wait: bool = True,
) -> dict[str, str]:
    """Create or update a CloudFormation stack (idempotent).

    Behavior:
    1. Check if stack exists
    2. If not: CreateStack
    3. If ROLLBACK_COMPLETE: delete then create
    4. If *_COMPLETE: UpdateStack (no-op if no changes)
    5. If wait: poll until terminal state
    6. Return stack outputs on success
    """
    client = session.client("cloudformation")
    template_body = template_path.read_text()

    cfn_params: list[dict[str, str]] = []
    if parameters:
        cfn_params = [
            {"ParameterKey": k, "ParameterValue": v}
            for k, v in parameters.items()
        ]

    cfn_tags: list[dict[str, str]] = []
    if tags:
        cfn_tags = [{"Key": k, "Value": v} for k, v in tags.items()]

    kwargs: dict = {
        "StackName": stack_name,
        "TemplateBody": template_body,
    }
    if cfn_params:
        kwargs["Parameters"] = cfn_params
    if capabilities:
        kwargs["Capabilities"] = capabilities
    if cfn_tags:
        kwargs["Tags"] = cfn_tags

    status = get_stack_status(session, stack_name)

    if status == "ROLLBACK_COMPLETE":
        info(f"Stack '{stack_name}' is in ROLLBACK_COMPLETE — deleting before recreate...")
        delete_stack(session, stack_name, wait=True)
        status = None

    if status is None:
        info(f"Creating stack '{stack_name}'...")
        client.create_stack(**kwargs)
        operation = "CREATE"
    elif status.endswith("_COMPLETE") or status.endswith("_FAILED"):
        info(f"Updating stack '{stack_name}' (current status: {status})...")
        try:
            client.update_stack(**kwargs)
            operation = "UPDATE"
        except ClientError as e:
            if "No updates are to be performed" in str(e):
                info(f"No changes detected for stack '{stack_name}'.")
                return get_stack_outputs(session, stack_name)
            raise
    else:
        raise click.ClickException(
            f"Stack '{stack_name}' is in non-terminal state '{status}'. "
            f"Wait for the current operation to complete, then retry."
        )

    if wait:
        final_status = _wait_for_stack(client, stack_name)
        expected = f"{operation}_COMPLETE"
        if final_status != expected:
            raise click.ClickException(
                f"Stack '{stack_name}' ended in state '{final_status}' (expected '{expected}'). "
                f"Check events: uv run deploy cfn-events --stack-name {stack_name}"
            )
        return get_stack_outputs(session, stack_name)

    return {}


def delete_stack(
    session: boto3.Session,
    stack_name: str,
    wait: bool = True,
) -> None:
    """Delete a CloudFormation stack."""
    client = session.client("cloudformation")

    status = get_stack_status(session, stack_name)
    if status is None:
        info(f"Stack '{stack_name}' does not exist. Nothing to delete.")
        return

    info(f"Deleting stack '{stack_name}'...")
    client.delete_stack(StackName=stack_name)

    if wait:
        final_status = _wait_for_stack(client, stack_name)
        if final_status == "DELETE_COMPLETE":
            info(f"Stack '{stack_name}' deleted successfully.")
        elif final_status == "DELETE_FAILED":
            raise click.ClickException(
                f"Stack '{stack_name}' deletion failed. "
                f"Check events: uv run deploy cfn-events --stack-name {stack_name}"
            )


def get_stack_outputs(
    session: boto3.Session,
    stack_name: str,
    output_key: str | None = None,
) -> dict[str, str] | str:
    """Get stack outputs. If output_key given, return single value."""
    client = session.client("cloudformation")
    try:
        response = client.describe_stacks(StackName=stack_name)
    except ClientError as e:
        if "does not exist" in str(e):
            raise click.ClickException(
                f"Stack '{stack_name}' does not exist. "
                f"Deploy it first with: uv run deploy cfn --stack-name {stack_name} --template <path>"
            )
        raise

    stacks = response.get("Stacks", [])
    if not stacks:
        raise click.ClickException(f"Stack '{stack_name}' not found.")

    raw_outputs = stacks[0].get("Outputs", [])
    outputs = {o["OutputKey"]: o["OutputValue"] for o in raw_outputs}

    if output_key:
        if output_key not in outputs:
            raise click.ClickException(
                f"Output key '{output_key}' not found in stack '{stack_name}'. "
                f"Available keys: {', '.join(outputs.keys()) if outputs else '(none)'}"
            )
        return outputs[output_key]

    return outputs


def get_stack_events(
    session: boto3.Session,
    stack_name: str,
    limit: int = 20,
) -> list[dict]:
    """Get recent stack events in chronological order."""
    client = session.client("cloudformation")
    try:
        response = client.describe_stack_events(StackName=stack_name)
    except ClientError as e:
        if "does not exist" in str(e):
            raise click.ClickException(
                f"Stack '{stack_name}' does not exist."
            )
        raise

    events = response.get("StackEvents", [])
    # Events come newest-first; reverse for chronological order, then take last N
    events.reverse()
    events = events[-limit:]

    return [
        {
            "Timestamp": str(e.get("Timestamp", "")),
            "LogicalResourceId": e.get("LogicalResourceId", ""),
            "ResourceStatus": e.get("ResourceStatus", ""),
            "ResourceStatusReason": e.get("ResourceStatusReason", ""),
        }
        for e in events
    ]


# Status filter: include all "alive" states (exclude DELETE_COMPLETE)
ACTIVE_STATES = [
    "CREATE_COMPLETE",
    "CREATE_IN_PROGRESS",
    "CREATE_FAILED",
    "UPDATE_COMPLETE",
    "UPDATE_IN_PROGRESS",
    "UPDATE_ROLLBACK_COMPLETE",
    "UPDATE_ROLLBACK_IN_PROGRESS",
    "ROLLBACK_COMPLETE",
    "ROLLBACK_IN_PROGRESS",
    "DELETE_IN_PROGRESS",
    "DELETE_FAILED",
    "IMPORT_COMPLETE",
    "IMPORT_IN_PROGRESS",
    "IMPORT_ROLLBACK_COMPLETE",
    "IMPORT_ROLLBACK_IN_PROGRESS",
    "REVIEW_IN_PROGRESS",
]


def list_managed_stacks(
    session: boto3.Session,
    namespace: str,
    env: str,
) -> list[dict[str, str]]:
    """List CloudFormation stacks managed by IPA for a namespace and environment.

    Discovers stacks matching the naming convention: {namespace}-{env}-{service}.
    Uses list_stacks with client-side prefix filtering.

    Returns list of dicts with keys: StackName, Service, StackStatus, CreatedTime, UpdatedTime.
    """
    client = session.client("cloudformation")
    prefix = f"{namespace}-{env}-"

    paginator = client.get_paginator("list_stacks")
    pages = paginator.paginate(StackStatusFilter=ACTIVE_STATES)

    stacks: list[dict[str, str]] = []
    for page in pages:
        for summary in page.get("StackSummaries", []):
            name = summary["StackName"]
            if not name.startswith(prefix):
                continue
            service = name[len(prefix):]
            stacks.append({
                "StackName": name,
                "Service": service,
                "StackStatus": summary["StackStatus"],
                "CreatedTime": str(summary.get("CreationTime", "")),
                "UpdatedTime": str(summary.get("LastUpdatedTime", "")),
            })

    # Sort by stack name for deterministic output
    stacks.sort(key=lambda s: s["StackName"])
    return stacks


def _wait_for_stack(
    client: object,
    stack_name: str,
    timeout_minutes: int = 60,
) -> str:
    """Poll stack status until terminal state or timeout."""
    deadline = time.monotonic() + timeout_minutes * 60
    while time.monotonic() < deadline:
        try:
            response = client.describe_stacks(StackName=stack_name)  # type: ignore[union-attr]
            stacks = response.get("Stacks", [])
            if not stacks:
                return "DELETE_COMPLETE"
            status = stacks[0]["StackStatus"]
        except ClientError as e:
            if "does not exist" in str(e):
                return "DELETE_COMPLETE"
            raise

        if status in TERMINAL_STATES:
            return status
        info(f"  Stack status: {status}...")
        time.sleep(5)

    raise click.ClickException(
        f"Timeout waiting for stack '{stack_name}' after {timeout_minutes} minutes. "
        f"Check events: uv run deploy cfn-events --stack-name {stack_name}"
    )


def parse_key_value_pairs(raw: str | None) -> dict[str, str] | None:
    """Parse 'Key1=Val1 Key2=Val2' into dict."""
    if not raw:
        return None
    pairs = {}
    for item in raw.split():
        if "=" not in item:
            raise click.BadParameter(f"Invalid format: '{item}'. Expected Key=Value")
        key, value = item.split("=", 1)
        pairs[key] = value
    return pairs
