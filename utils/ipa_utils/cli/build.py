"""Application build commands.

Entry point: uv run build <subcommand>

Subcommands:
    docker    Build Docker image and optionally push to ECR

CLI parsing only. Business logic in ipa_utils.aws.ecr.
"""

import click

from ipa_utils.aws.cloudformation import get_boto3_session
from ipa_utils.aws.ecr import authenticate_ecr, build_image, push_image


@click.group()
def main() -> None:
    """Application build operations."""


@main.command()
@click.option("--tag", required=True, help="Image tag name")
@click.option("--dockerfile", default="Dockerfile", type=click.Path(), help="Path to Dockerfile")
@click.option("--context", default=".", type=click.Path(), help="Docker build context directory")
@click.option("--ecr-repo", default=None, help="ECR repository URI (authenticates and pushes if provided)")
@click.option("--region", default=None, envvar="AWS_DEFAULT_REGION", help="AWS region (for ECR auth)")
@click.option("--profile", default=None, help="AWS CLI profile name (for ECR auth)")
@click.option("--platform", default="linux/amd64", help="Target platform")
@click.option("--build-arg", multiple=True, help="Build arguments (repeatable)")
def docker(
    tag: str,
    dockerfile: str,
    context: str,
    ecr_repo: str | None,
    region: str | None,
    profile: str | None,
    platform: str,
    build_arg: tuple[str, ...],
) -> None:
    """Build Docker image and optionally push to ECR."""
    build_image(
        tag=tag,
        dockerfile=dockerfile,
        context=context,
        platform=platform,
        build_args=build_arg,
    )

    if ecr_repo:
        session = get_boto3_session(profile=profile, region=region)
        authenticate_ecr(session=session, registry=ecr_repo)
        push_image(tag=tag, ecr_repo=ecr_repo)
