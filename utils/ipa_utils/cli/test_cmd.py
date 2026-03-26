"""Test execution commands.

Entry point: uv run test <subcommand>

Subcommands:
    unit      Run pytest unit tests
    security  Run ASH security scans
    cfn-lint  Validate CloudFormation templates

CLI parsing only. Test execution via subprocess or Python API.

Note: Module named test_cmd.py (not test.py) to avoid collision
with Python's stdlib test package.
"""

import shutil
import subprocess
from pathlib import Path

import click

from ipa_utils.helpers.output import info, error, result


@click.group()
def main() -> None:
    """Test execution operations."""


@main.command()
@click.option("--path", default="tests/", help="Test directory or file")
@click.option("--markers", default=None, help="Pytest marker expression")
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("--coverage", is_flag=True, help="Collect coverage")
def unit(
    path: str,
    markers: str | None,
    verbose: bool,
    coverage: bool,
) -> None:
    """Run pytest unit tests."""
    cmd = ["python", "-m", "pytest", path]
    if markers:
        cmd.extend(["-m", markers])
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov", "--cov-report=term-missing"])
    proc = subprocess.run(cmd)  # nosec B603 — list invocation, no shell
    raise SystemExit(proc.returncode)


@main.command()
@click.option("--target", default="infra/", help="Directory to scan")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]), help="Output format")
def security(
    target: str,
    output_format: str,
) -> None:
    """Run ASH security scans."""
    ash_path = shutil.which("ash")
    if not ash_path:
        raise click.ClickException(
            "ASH (Automated Security Helper) not found. "
            "Install from: https://github.com/awslabs/automated-security-helper"
        )

    cmd = [ash_path, "--source-dir", target]
    if output_format == "json":
        cmd.extend(["--output-format", "json"])

    info(f"Running ASH security scan on: {target}")
    proc = subprocess.run(cmd)  # nosec B603 — list invocation, no shell
    raise SystemExit(proc.returncode)


@main.command("cfn-lint")
@click.option("--template", default=None, type=click.Path(exists=True), help="Specific template to validate")
@click.option("--directory", default=None, type=click.Path(exists=True), help="Template directory to validate")
def cfn_lint_cmd(
    template: str | None,
    directory: str | None,
) -> None:
    """Validate CloudFormation templates with cfn-lint."""
    if not template and not directory:
        directory = "infra/cfn/"
        if not Path(directory).exists():
            raise click.ClickException(
                "No template or directory specified, and default 'infra/cfn/' does not exist."
            )

    from cfnlint import decode, runner as cfn_runner
    from cfnlint.config import ConfigMixIn

    templates: list[str] = []
    if template:
        templates.append(template)
    if directory:
        dir_path = Path(directory)
        templates.extend(
            str(p) for p in dir_path.glob("**/*.yml")
        )
        templates.extend(
            str(p) for p in dir_path.glob("**/*.yaml")
        )

    if not templates:
        info("No templates found to validate.")
        return

    total_errors = 0
    for tmpl in templates:
        info(f"Validating: {tmpl}")
        try:
            config = ConfigMixIn(["--template", tmpl])
            matches = list(cfn_runner.Runner(config).run())
            if matches:
                for match in matches:
                    error(str(match))
                total_errors += len(matches)
            else:
                result(f"  {tmpl}: OK")
        except Exception as e:
            error(f"  {tmpl}: {e}")
            total_errors += 1

    if total_errors > 0:
        raise click.ClickException(f"cfn-lint found {total_errors} issue(s)")
    else:
        info(f"All {len(templates)} template(s) passed validation.")
