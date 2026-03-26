"""Tests for deploy cfn-generate — dynamic template generation."""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from ipa_utils.aws.cfn_template import generate_security_template, write_template
from ipa_utils.cli.deploy import main


class TestGenerateSecurityTemplate:
    """Tests for generate_security_template()."""

    def test_generates_valid_yaml(self):
        """Generated template is valid YAML."""
        content = generate_security_template(
            namespace="testproject",
            env="dev",
            account_id="123456789012",
            managed_policy="AdministratorAccess",
        )
        template = yaml.safe_load(content)
        assert template["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_has_builder_role(self):
        """Generated template includes BuilderExecutionRole."""
        content = generate_security_template(
            namespace="testproject",
            env="dev",
            account_id="123456789012",
        )
        template = yaml.safe_load(content)
        assert "BuilderExecutionRole" in template["Resources"]

    def test_has_codebuild_role(self):
        """Generated template includes CodeBuildExecutionRole."""
        content = generate_security_template(
            namespace="testproject",
            env="dev",
            account_id="123456789012",
        )
        template = yaml.safe_load(content)
        assert "CodeBuildExecutionRole" in template["Resources"]

    def test_managed_policy_attached(self):
        """Managed policy is attached to both roles."""
        content = generate_security_template(
            namespace="testproject",
            env="dev",
            account_id="123456789012",
            managed_policy="PowerUserAccess",
        )
        template = yaml.safe_load(content)
        builder_policies = template["Resources"]["BuilderExecutionRole"]["Properties"]["ManagedPolicyArns"]
        assert "arn:aws:iam::aws:policy/PowerUserAccess" in builder_policies

    def test_existing_role_arn(self):
        """With role_arn, template just outputs the ARN."""
        content = generate_security_template(
            namespace="testproject",
            env="dev",
            account_id="123456789012",
            role_arn="arn:aws:iam::123456789012:role/existing-role",
        )
        template = yaml.safe_load(content)
        assert "Resources" not in template
        assert template["Outputs"]["BuilderRoleArn"]["Value"] == "arn:aws:iam::123456789012:role/existing-role"

    def test_default_policy_when_none(self):
        """Default policy is ReadOnlyAccess when no managed policy specified."""
        content = generate_security_template(
            namespace="testproject",
            env="dev",
            account_id="123456789012",
        )
        template = yaml.safe_load(content)
        builder_policies = template["Resources"]["BuilderExecutionRole"]["Properties"]["ManagedPolicyArns"]
        assert "arn:aws:iam::aws:policy/ReadOnlyAccess" in builder_policies


class TestWriteTemplate:
    """Tests for write_template()."""

    def test_writes_to_disk(self, tmp_path):
        """Template is written to the specified path."""
        out = tmp_path / "generated" / "security.yml"
        write_template("test content", out)
        assert out.exists()
        assert out.read_text() == "test content"

    def test_creates_parent_directories(self, tmp_path):
        """Parent directories are created if they don't exist."""
        out = tmp_path / "deep" / "nested" / "template.yml"
        write_template("content", out)
        assert out.exists()


class TestCfnGenerateCLI:
    """CLI tests for deploy cfn-generate."""

    def test_generate_security(self, tmp_path):
        """deploy cfn-generate creates a security template."""
        output = tmp_path / "security.yml"
        runner = CliRunner()
        result = runner.invoke(main, [
            "cfn-generate",
            "--template-type", "security",
            "--namespace", "testproject",
            "--env", "dev",
            "--account-id", "123456789012",
            "--managed-policy", "AdministratorAccess",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()
        template = yaml.safe_load(output.read_text())
        assert "BuilderExecutionRole" in template["Resources"]

    def test_generate_with_role_arn(self, tmp_path):
        """deploy cfn-generate with --role-arn skips role creation."""
        output = tmp_path / "security.yml"
        runner = CliRunner()
        result = runner.invoke(main, [
            "cfn-generate",
            "--template-type", "security",
            "--namespace", "testproject",
            "--env", "dev",
            "--account-id", "123456789012",
            "--role-arn", "arn:aws:iam::123456789012:role/existing",
            "--output", str(output),
        ])
        assert result.exit_code == 0
        template = yaml.safe_load(output.read_text())
        assert "Resources" not in template
