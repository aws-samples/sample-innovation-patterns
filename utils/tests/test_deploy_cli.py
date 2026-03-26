"""CLI integration tests for deploy commands using CliRunner + moto."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from moto import mock_aws

from ipa_utils.cli.deploy import main
from tests.conftest import SIMPLE_STACK_TEMPLATE


@pytest.fixture
def runner():
    return CliRunner()


class TestDeployCfnCLI:
    """CLI tests for deploy cfn."""

    @mock_aws
    def test_cfn_create(self, runner):
        """deploy cfn creates a stack and exits 0."""
        result = runner.invoke(main, [
            "cfn",
            "--stack-name", "cli-test-stack",
            "--template", str(SIMPLE_STACK_TEMPLATE),
            "--region", "us-east-1",
        ], env={"AWS_DEFAULT_REGION": "us-east-1"})
        assert result.exit_code == 0

    @mock_aws
    def test_cfn_with_parameters(self, runner):
        """deploy cfn accepts parameter-overrides."""
        result = runner.invoke(main, [
            "cfn",
            "--stack-name", "cli-param-stack",
            "--template", str(SIMPLE_STACK_TEMPLATE),
            "--parameter-overrides", "TableName=my-table",
            "--region", "us-east-1",
        ])
        assert result.exit_code == 0

    @mock_aws
    def test_cfn_missing_template(self, runner):
        """deploy cfn fails with missing template file."""
        result = runner.invoke(main, [
            "cfn",
            "--stack-name", "cli-test",
            "--template", "/nonexistent/template.yml",
        ])
        assert result.exit_code != 0


class TestDeployCfnDeleteCLI:
    """CLI tests for deploy cfn-delete."""

    @mock_aws
    def test_cfn_delete_existing(self, runner):
        """deploy cfn-delete deletes a stack."""
        # Create first
        runner.invoke(main, [
            "cfn",
            "--stack-name", "cli-delete-stack",
            "--template", str(SIMPLE_STACK_TEMPLATE),
            "--region", "us-east-1",
        ])
        # Delete
        result = runner.invoke(main, [
            "cfn-delete",
            "--stack-name", "cli-delete-stack",
            "--region", "us-east-1",
        ])
        assert result.exit_code == 0

    @mock_aws
    def test_cfn_delete_nonexistent(self, runner):
        """deploy cfn-delete on nonexistent stack is a no-op."""
        result = runner.invoke(main, [
            "cfn-delete",
            "--stack-name", "nonexistent",
            "--region", "us-east-1",
        ])
        assert result.exit_code == 0


class TestDeployCfnOutputsCLI:
    """CLI tests for deploy cfn-outputs."""

    @mock_aws
    def test_cfn_outputs_text(self, runner):
        """deploy cfn-outputs prints outputs in text format."""
        runner.invoke(main, [
            "cfn",
            "--stack-name", "cli-outputs-stack",
            "--template", str(SIMPLE_STACK_TEMPLATE),
            "--region", "us-east-1",
        ])
        result = runner.invoke(main, [
            "cfn-outputs",
            "--stack-name", "cli-outputs-stack",
            "--region", "us-east-1",
        ])
        assert result.exit_code == 0

    @mock_aws
    def test_cfn_outputs_json(self, runner):
        """deploy cfn-outputs prints outputs in JSON format."""
        runner.invoke(main, [
            "cfn",
            "--stack-name", "cli-outputs-json",
            "--template", str(SIMPLE_STACK_TEMPLATE),
            "--region", "us-east-1",
        ])
        result = runner.invoke(main, [
            "cfn-outputs",
            "--stack-name", "cli-outputs-json",
            "--format", "json",
            "--region", "us-east-1",
        ])
        assert result.exit_code == 0

    @mock_aws
    def test_cfn_outputs_missing_stack(self, runner):
        """deploy cfn-outputs on nonexistent stack exits 1."""
        result = runner.invoke(main, [
            "cfn-outputs",
            "--stack-name", "nonexistent",
            "--region", "us-east-1",
        ])
        assert result.exit_code != 0


class TestDeployCfnStatusCLI:
    """CLI tests for deploy cfn-status."""

    @mock_aws
    def test_cfn_status_existing(self, runner):
        """deploy cfn-status prints status for existing stack."""
        runner.invoke(main, [
            "cfn",
            "--stack-name", "cli-status-stack",
            "--template", str(SIMPLE_STACK_TEMPLATE),
            "--region", "us-east-1",
        ])
        result = runner.invoke(main, [
            "cfn-status",
            "--stack-name", "cli-status-stack",
            "--region", "us-east-1",
        ])
        assert result.exit_code == 0
        assert "CREATE_COMPLETE" in result.output

    @mock_aws
    def test_cfn_status_nonexistent(self, runner):
        """deploy cfn-status prints DOES_NOT_EXIST and exits 1."""
        result = runner.invoke(main, [
            "cfn-status",
            "--stack-name", "nonexistent",
            "--region", "us-east-1",
        ])
        assert result.exit_code == 1
        assert "DOES_NOT_EXIST" in result.output


class TestDeployCfnEventsCLI:
    """CLI tests for deploy cfn-events."""

    @mock_aws
    def test_cfn_events_existing(self, runner):
        """deploy cfn-events prints events for existing stack."""
        runner.invoke(main, [
            "cfn",
            "--stack-name", "cli-events-stack",
            "--template", str(SIMPLE_STACK_TEMPLATE),
            "--region", "us-east-1",
        ])
        result = runner.invoke(main, [
            "cfn-events",
            "--stack-name", "cli-events-stack",
            "--region", "us-east-1",
        ])
        assert result.exit_code == 0
        assert "Timestamp" in result.output or "LogicalResourceId" in result.output

    @mock_aws
    def test_cfn_events_nonexistent(self, runner):
        """deploy cfn-events on nonexistent stack exits 1."""
        result = runner.invoke(main, [
            "cfn-events",
            "--stack-name", "nonexistent",
            "--region", "us-east-1",
        ])
        assert result.exit_code != 0


class TestDeployCfnListCLI:
    """CLI tests for deploy cfn-list."""

    @mock_aws
    def test_lists_stacks_text_format(self, runner):
        """deploy cfn-list prints matching stacks as a table."""
        runner.invoke(main, [
            "cfn",
            "--stack-name", "ns-dev-security",
            "--template", str(SIMPLE_STACK_TEMPLATE),
            "--parameter-overrides", "TableName=table-ns-dev-security",
            "--region", "us-east-1",
        ], env={"AWS_DEFAULT_REGION": "us-east-1"})

        result = runner.invoke(main, [
            "cfn-list",
            "--namespace", "ns",
            "--env", "dev",
            "--region", "us-east-1",
        ], env={"AWS_DEFAULT_REGION": "us-east-1"})

        assert result.exit_code == 0
        assert "ns-dev-security" in result.output

    @mock_aws
    def test_lists_stacks_json_format(self, runner):
        """deploy cfn-list --format json returns valid JSON array."""
        runner.invoke(main, [
            "cfn",
            "--stack-name", "ns-dev-db",
            "--template", str(SIMPLE_STACK_TEMPLATE),
            "--parameter-overrides", "TableName=table-ns-dev-db",
            "--region", "us-east-1",
        ], env={"AWS_DEFAULT_REGION": "us-east-1"})

        result = runner.invoke(main, [
            "cfn-list",
            "--namespace", "ns",
            "--env", "dev",
            "--format", "json",
            "--region", "us-east-1",
        ], env={"AWS_DEFAULT_REGION": "us-east-1"})

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["StackName"] == "ns-dev-db"

    @mock_aws
    def test_no_stacks_found(self, runner):
        """deploy cfn-list with no matches exits 0."""
        result = runner.invoke(main, [
            "cfn-list",
            "--namespace", "empty",
            "--env", "dev",
            "--region", "us-east-1",
        ], env={"AWS_DEFAULT_REGION": "us-east-1"})

        assert result.exit_code == 0
