"""Tests for test cfn-lint — CloudFormation template validation."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from ipa_utils.cli.test_cmd import main
from tests.conftest import SIMPLE_STACK_TEMPLATE, FIXTURES_DIR


class TestCfnLintCLI:
    """CLI tests for test cfn-lint."""

    def test_validate_single_template(self):
        """test cfn-lint validates a specific template."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "cfn-lint",
            "--template", str(SIMPLE_STACK_TEMPLATE),
        ])
        # Should succeed (our fixture template is valid)
        assert result.exit_code == 0

    def test_validate_directory(self):
        """test cfn-lint validates all templates in a directory."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "cfn-lint",
            "--directory", str(FIXTURES_DIR),
        ])
        assert result.exit_code == 0

    def test_invalid_template(self, tmp_path):
        """test cfn-lint fails on an invalid template."""
        bad_template = tmp_path / "bad.yml"
        bad_template.write_text("Resources:\n  Bad:\n    Type: AWS::Invalid::Resource\n")
        runner = CliRunner()
        result = runner.invoke(main, [
            "cfn-lint",
            "--template", str(bad_template),
        ])
        assert result.exit_code != 0
