"""Tests for test unit — pytest wrapper."""

from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from ipa_utils.cli.test_cmd import main


class TestUnitCLI:
    """CLI tests for test unit."""

    @patch("ipa_utils.cli.test_cmd.subprocess.run")
    def test_basic_invocation(self, mock_run):
        """test unit invokes pytest."""
        mock_run.return_value = MagicMock(returncode=0)
        runner = CliRunner()
        result = runner.invoke(main, ["unit"])
        assert result.exit_code == 0
        cmd = mock_run.call_args[0][0]
        assert "pytest" in cmd

    @patch("ipa_utils.cli.test_cmd.subprocess.run")
    def test_with_path(self, mock_run):
        """test unit accepts custom path."""
        mock_run.return_value = MagicMock(returncode=0)
        runner = CliRunner()
        result = runner.invoke(main, ["unit", "--path", "tests/specific/"])
        cmd = mock_run.call_args[0][0]
        assert "tests/specific/" in cmd

    @patch("ipa_utils.cli.test_cmd.subprocess.run")
    def test_with_markers(self, mock_run):
        """test unit passes markers to pytest."""
        mock_run.return_value = MagicMock(returncode=0)
        runner = CliRunner()
        result = runner.invoke(main, ["unit", "--markers", "not integration"])
        cmd = mock_run.call_args[0][0]
        assert "-m" in cmd
        assert "not integration" in cmd

    @patch("ipa_utils.cli.test_cmd.subprocess.run")
    def test_verbose_and_coverage(self, mock_run):
        """test unit passes verbose and coverage flags."""
        mock_run.return_value = MagicMock(returncode=0)
        runner = CliRunner()
        result = runner.invoke(main, ["unit", "--verbose", "--coverage"])
        cmd = mock_run.call_args[0][0]
        assert "-v" in cmd
        assert "--cov" in cmd

    @patch("ipa_utils.cli.test_cmd.subprocess.run")
    def test_failure_propagates(self, mock_run):
        """test unit propagates pytest exit code."""
        mock_run.return_value = MagicMock(returncode=1)
        runner = CliRunner()
        result = runner.invoke(main, ["unit"])
        assert result.exit_code == 1
