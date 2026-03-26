"""Shared test fixtures for IPA utilities."""

from pathlib import Path

import boto3
import pytest
from click.testing import CliRunner
from moto import mock_aws


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SIMPLE_STACK_TEMPLATE = FIXTURES_DIR / "simple-stack.yml"


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def aws_session():
    """Mocked AWS session via moto."""
    with mock_aws():
        session = boto3.Session(region_name="us-east-1")
        # Ensure STS identity exists for moto
        session.client("sts").get_caller_identity()
        yield session


@pytest.fixture
def cfn_client(aws_session):
    """Mocked CloudFormation client."""
    return aws_session.client("cloudformation")


@pytest.fixture
def template_path() -> Path:
    """Path to the simple test template."""
    return SIMPLE_STACK_TEMPLATE
