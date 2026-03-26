"""Tests for test security — ASH wrapper."""

from unittest.mock import patch, MagicMock

import click
import pytest
from click.testing import CliRunner

from ipa_utils.cli.test_cmd import main


class TestSecurityCLI:
    """CLI tests for test security."""

    @patch("ipa_utils.cli.test_cmd.shutil.which", return_value=None)
    def test_ash_not_found(self, mock_which):
        """test security raises error when ASH is not installed."""
        runner = CliRunner()
        result = runner.invoke(main, ["security"])
        assert result.exit_code != 0
        assert "ASH" in result.output

    @patch("ipa_utils.cli.test_cmd.subprocess.run")
    @patch("ipa_utils.cli.test_cmd.shutil.which", return_value="/usr/local/bin/ash")
    def test_ash_found(self, mock_which, mock_run):
        """test security invokes ASH when found."""
        mock_run.return_value = MagicMock(returncode=0)
        runner = CliRunner()
        result = runner.invoke(main, ["security"])
        assert result.exit_code == 0
        mock_run.assert_called_once()

    @patch("ipa_utils.cli.test_cmd.subprocess.run")
    @patch("ipa_utils.cli.test_cmd.shutil.which", return_value="/usr/local/bin/ash")
    def test_custom_target(self, mock_which, mock_run):
        """test security accepts custom target directory."""
        mock_run.return_value = MagicMock(returncode=0)
        runner = CliRunner()
        result = runner.invoke(main, ["security", "--target", "custom/dir/"])
        cmd = mock_run.call_args[0][0]
        assert "custom/dir/" in cmd
