"""ECR authentication and Docker image operations.

Functions:
    authenticate_ecr()  — Get ECR auth token and docker login
    build_image()       — Run docker build via subprocess
    push_image()        — Tag and push to ECR

Uses subprocess for Docker CLI operations (KISS — Docker SDK is heavy).
"""

import base64
import subprocess

import boto3
import click

from ipa_utils.helpers.output import info


def authenticate_ecr(session: boto3.Session, registry: str) -> None:
    """Authenticate Docker to an ECR registry.

    Gets an ECR authorization token and runs docker login.
    """
    client = session.client("ecr")
    response = client.get_authorization_token()
    auth_data = response["authorizationData"][0]
    token = base64.b64decode(auth_data["authorizationToken"]).decode()
    username, password = token.split(":", 1)
    endpoint = auth_data["proxyEndpoint"]

    result = subprocess.run(
        ["docker", "login", "--username", username, "--password-stdin", endpoint],
        input=password,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise click.ClickException(f"Docker login failed: {result.stderr.strip()}")
    info(f"Authenticated to ECR: {endpoint}")


def build_image(
    tag: str,
    dockerfile: str = "Dockerfile",
    context: str = ".",
    platform: str = "linux/amd64",
    build_args: tuple[str, ...] = (),
) -> None:
    """Build a Docker image via subprocess."""
    cmd = [
        "docker", "build",
        "-t", tag,
        "-f", dockerfile,
        "--platform", platform,
    ]
    for arg in build_args:
        cmd.extend(["--build-arg", arg])
    cmd.append(context)

    info(f"Building image: {tag}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise click.ClickException(f"Docker build failed (exit {result.returncode})")
    info(f"Image built: {tag}")


def push_image(tag: str, ecr_repo: str) -> None:
    """Tag and push a Docker image to ECR."""
    ecr_tag = f"{ecr_repo}:{tag}"

    # Tag for ECR
    result = subprocess.run(["docker", "tag", tag, ecr_tag])
    if result.returncode != 0:
        raise click.ClickException(f"Docker tag failed (exit {result.returncode})")

    # Push
    info(f"Pushing image: {ecr_tag}")
    result = subprocess.run(["docker", "push", ecr_tag])
    if result.returncode != 0:
        raise click.ClickException(f"Docker push failed (exit {result.returncode})")
    info(f"Image pushed: {ecr_tag}")
