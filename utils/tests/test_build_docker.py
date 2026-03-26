"""Tests for build docker — Docker build + ECR push."""

from unittest.mock import patch, MagicMock

import click
import pytest
from click.testing import CliRunner

from ipa_utils.aws.ecr import build_image, push_image
from ipa_utils.cli.build import main


class TestBuildImage:
    """Tests for build_image()."""

    @patch("ipa_utils.aws.ecr.subprocess.run")
    def test_basic_build(self, mock_run):
        """Builds an image with default options."""
        mock_run.return_value = MagicMock(returncode=0)
        build_image(tag="test-image")
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "docker" in cmd
        assert "build" in cmd
        assert "-t" in cmd
        assert "test-image" in cmd

    @patch("ipa_utils.aws.ecr.subprocess.run")
    def test_build_with_options(self, mock_run):
        """Builds with custom dockerfile, context, platform, and build args."""
        mock_run.return_value = MagicMock(returncode=0)
        build_image(
            tag="custom-image",
            dockerfile="custom.Dockerfile",
            context="src/",
            platform="linux/arm64",
            build_args=("NODE_ENV=production",),
        )
        cmd = mock_run.call_args[0][0]
        assert "-f" in cmd
        assert "custom.Dockerfile" in cmd
        assert "--platform" in cmd
        assert "linux/arm64" in cmd
        assert "--build-arg" in cmd
        assert "NODE_ENV=production" in cmd
        assert cmd[-1] == "src/"

    @patch("ipa_utils.aws.ecr.subprocess.run")
    def test_build_failure(self, mock_run):
        """Build failure raises ClickException."""
        mock_run.return_value = MagicMock(returncode=1)
        with pytest.raises(click.ClickException, match="Docker build failed"):
            build_image(tag="fail-image")


class TestPushImage:
    """Tests for push_image()."""

    @patch("ipa_utils.aws.ecr.subprocess.run")
    def test_tag_and_push(self, mock_run):
        """Tags and pushes image to ECR."""
        mock_run.return_value = MagicMock(returncode=0)
        push_image(tag="my-image", ecr_repo="123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo")
        assert mock_run.call_count == 2  # tag + push

    @patch("ipa_utils.aws.ecr.subprocess.run")
    def test_push_failure(self, mock_run):
        """Push failure raises ClickException."""
        # Tag succeeds, push fails
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=1),
        ]
        with pytest.raises(click.ClickException, match="Docker push failed"):
            push_image(tag="fail-image", ecr_repo="repo.ecr.us-east-1.amazonaws.com/repo")


class TestBuildDockerCLI:
    """CLI tests for build docker."""

    @patch("ipa_utils.cli.build.build_image")
    def test_basic_build_cli(self, mock_build):
        """build docker invokes build_image."""
        runner = CliRunner()
        result = runner.invoke(main, ["docker", "--tag", "test-image"])
        assert result.exit_code == 0
        mock_build.assert_called_once()

    @patch("ipa_utils.cli.build.build_image")
    @patch("ipa_utils.cli.build.authenticate_ecr")
    @patch("ipa_utils.cli.build.push_image")
    def test_build_with_ecr(self, mock_push, mock_auth, mock_build):
        """build docker with --ecr-repo authenticates and pushes."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "docker",
            "--tag", "test-image",
            "--ecr-repo", "123456789012.dkr.ecr.us-east-1.amazonaws.com/repo",
            "--region", "us-east-1",
        ])
        assert result.exit_code == 0
        mock_build.assert_called_once()
        mock_auth.assert_called_once()
        mock_push.assert_called_once()
