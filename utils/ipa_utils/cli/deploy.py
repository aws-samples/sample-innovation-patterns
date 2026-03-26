"""CloudFormation deployment commands.

Entry point: uv run deploy <subcommand>

Subcommands:
    cfn          Create or update a CloudFormation stack
    cfn-delete   Delete a CloudFormation stack
    cfn-outputs  Retrieve stack outputs
    cfn-status   Check stack existence and status
    cfn-events   Read recent stack events
    cfn-generate Generate a dynamic CloudFormation template

CLI parsing only. Business logic in ipa_utils.aws.cloudformation.
"""

import json
import sys
from pathlib import Path

import click

from ipa_utils.aws.cloudformation import (
    create_or_update_stack,
    delete_stack,
    get_boto3_session,
    get_stack_events,
    get_stack_outputs,
    get_stack_status,
    parse_key_value_pairs,
)
from ipa_utils.helpers.output import info, result, table


@click.group()
def main() -> None:
    """CloudFormation stack deployment operations."""


@main.command()
@click.option("--stack-name", required=True, help="CloudFormation stack name")
@click.option("--template", required=True, type=click.Path(exists=True), help="Path to CFN template")
@click.option("--parameter-overrides", default=None, help="Space-separated Key=Value pairs")
@click.option("--capabilities", default=None, help="CFN capabilities (e.g., CAPABILITY_NAMED_IAM)")
@click.option("--region", default=None, envvar="AWS_DEFAULT_REGION", help="AWS region")
@click.option("--profile", default=None, help="AWS CLI profile name")
@click.option("--wait/--no-wait", default=True, help="Wait for operation to complete")
@click.option("--tags", default=None, help="Space-separated Key=Value tag pairs")
def cfn(
    stack_name: str,
    template: str,
    parameter_overrides: str | None,
    capabilities: str | None,
    region: str | None,
    profile: str | None,
    wait: bool,
    tags: str | None,
) -> None:
    """Create or update a CloudFormation stack."""
    session = get_boto3_session(profile=profile, region=region)
    params = parse_key_value_pairs(parameter_overrides)
    tag_dict = parse_key_value_pairs(tags)
    caps = capabilities.split() if capabilities else None

    outputs = create_or_update_stack(
        session=session,
        stack_name=stack_name,
        template_path=Path(template),
        parameters=params,
        capabilities=caps,
        tags=tag_dict,
        wait=wait,
    )

    if outputs:
        info(f"\nStack '{stack_name}' outputs:")
        headers = ["OutputKey", "OutputValue"]
        rows = [[k, v] for k, v in outputs.items()]
        table(headers, rows)


@main.command("cfn-delete")
@click.option("--stack-name", required=True, help="CloudFormation stack name")
@click.option("--region", default=None, envvar="AWS_DEFAULT_REGION", help="AWS region")
@click.option("--profile", default=None, help="AWS CLI profile name")
@click.option("--wait/--no-wait", default=True, help="Wait for deletion to complete")
def cfn_delete(
    stack_name: str,
    region: str | None,
    profile: str | None,
    wait: bool,
) -> None:
    """Delete a CloudFormation stack."""
    session = get_boto3_session(profile=profile, region=region)
    delete_stack(session=session, stack_name=stack_name, wait=wait)


@main.command("cfn-outputs")
@click.option("--stack-name", required=True, help="CloudFormation stack name")
@click.option("--output-key", default=None, help="Specific output key (prints all if omitted)")
@click.option("--region", default=None, envvar="AWS_DEFAULT_REGION", help="AWS region")
@click.option("--profile", default=None, help="AWS CLI profile name")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json", "env"]), help="Output format")
def cfn_outputs(
    stack_name: str,
    output_key: str | None,
    region: str | None,
    profile: str | None,
    output_format: str,
) -> None:
    """Retrieve stack outputs."""
    session = get_boto3_session(profile=profile, region=region)
    outputs = get_stack_outputs(session=session, stack_name=stack_name, output_key=output_key)

    # Single key requested — print raw value
    if isinstance(outputs, str):
        result(outputs)
        return

    # All outputs
    if output_format == "json":
        result(json.dumps(outputs, indent=2))
    elif output_format == "env":
        for k, v in outputs.items():
            result(f"{k}={v}")
    else:  # text
        for k, v in outputs.items():
            result(f"{k}: {v}")


@main.command("cfn-status")
@click.option("--stack-name", required=True, help="CloudFormation stack name")
@click.option("--region", default=None, envvar="AWS_DEFAULT_REGION", help="AWS region")
@click.option("--profile", default=None, help="AWS CLI profile name")
def cfn_status(
    stack_name: str,
    region: str | None,
    profile: str | None,
) -> None:
    """Check stack existence and status."""
    session = get_boto3_session(profile=profile, region=region)
    status = get_stack_status(session=session, stack_name=stack_name)

    if status is None:
        result("DOES_NOT_EXIST")
        sys.exit(1)
    else:
        result(status)


@main.command("cfn-events")
@click.option("--stack-name", required=True, help="CloudFormation stack name")
@click.option("--limit", default=20, help="Number of events to display")
@click.option("--region", default=None, envvar="AWS_DEFAULT_REGION", help="AWS region")
@click.option("--profile", default=None, help="AWS CLI profile name")
def cfn_events(
    stack_name: str,
    limit: int,
    region: str | None,
    profile: str | None,
) -> None:
    """Read recent stack events."""
    session = get_boto3_session(profile=profile, region=region)
    events = get_stack_events(session=session, stack_name=stack_name, limit=limit)

    if not events:
        info("No events found.")
        return

    headers = ["Timestamp", "LogicalResourceId", "Status", "StatusReason"]
    rows = [
        [
            e["Timestamp"][:19] if len(e["Timestamp"]) > 19 else e["Timestamp"],
            e["LogicalResourceId"],
            e["ResourceStatus"],
            e["ResourceStatusReason"],
        ]
        for e in events
    ]
    table(headers, rows)


@main.command("cfn-generate")
@click.option("--template-type", required=True, type=click.Choice(["security"]), help="Template type to generate")
@click.option("--namespace", required=True, help="Project namespace")
@click.option("--env", required=True, help="Environment (dev/staging/prod)")
@click.option("--account-id", required=True, help="12-digit AWS account ID")
@click.option("--output", "output_path", required=True, type=click.Path(), help="Output file path")
@click.option("--managed-policy", default=None, help="AWS managed policy name")
@click.option("--role-arn", default=None, help="Existing role ARN (skip role creation)")
def cfn_generate(
    template_type: str,
    namespace: str,
    env: str,
    account_id: str,
    output_path: str,
    managed_policy: str | None,
    role_arn: str | None,
) -> None:
    """Generate a dynamic CloudFormation template."""
    from ipa_utils.aws.cfn_template import generate_security_template, write_template

    if template_type == "security":
        content = generate_security_template(
            namespace=namespace,
            env=env,
            account_id=account_id,
            managed_policy=managed_policy,
            role_arn=role_arn,
        )
    else:
        raise click.ClickException(f"Unknown template type: {template_type}")

    out = Path(output_path)
    write_template(content, out)
    info(f"Generated {template_type} template: {out}")
    result(str(out))
