"""Report which of a run's resources are still live, and leave a durable pointer.

``live_stacks`` returns ``(stacks, error)`` and **never raises**. It runs at session
teardown, where an exception replaces the standing-resource report — the record of
what is still costing money — with a fixture error. It is also what lets
``conftest.py`` express the preservation rule without a ``try``:

    preserve  if  live_stacks(ns) is non-empty  OR  the listing errored

The pointer is written at the **harness root** — one level above this module, beside
the Makefile — inside the repository directory rather than into the temp project,
because macOS may reclaim ``$TMPDIR``. And it is written to be
readable with **no credentials configured**: its whole purpose is to survive a lost
terminal, so a pointer needing a working credential chain to interpret fails exactly
when it is needed.
"""

from __future__ import annotations

import subprocess  # nosec B404 - argv lists only, shell=False; see .ash/ash.yaml
from pathlib import Path

from harness import aws

# ``parents[1]``, NOT ``parent``: this module lives in ``harness/`` but the pointer it
# writes must land at the HARNESS ROOT. Three things already assert that location and
# none of them fails loudly if it moves -- ``.gitignore``'s glob stops matching,
# ``README.md``'s "beside this README" claim becomes false, and the deployed buildspec
# collects no artifact.
HERE = Path(__file__).resolve().parents[1]

HEALTHY_STATES = frozenset(
    {"CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"}
)


def pointer_path(namespace: str) -> Path:
    """Where the pointer for ``namespace`` lives: beside the Makefile."""
    return HERE / f"standing-resources-{namespace}.md"


def parse_env(env_file: Path) -> dict[str, str]:
    """Parse one ``.env``. Deliberately no run-folder merge.

    A merge across run folders means the values reported belong to no single run,
    which is the opposite of what a standing-resource report is for.
    """
    values: dict[str, str] = {}
    if not env_file.is_file():
        return values
    for raw in env_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def live_stacks(
    namespace: str, region: str = aws.REGION
) -> tuple[list[tuple[str, str]], str]:
    """Every live stack under ``namespace``, as ``(name, status)`` pairs.

    Returns ``(stacks, error)`` and NEVER raises. An empty list with an empty error
    means "nothing standing"; an empty list with a non-empty error means "unknown",
    and callers must treat those differently — the preservation rule preserves on
    error precisely because a listing that failed is the case where standing stacks
    are most likely.
    """
    try:
        proc = subprocess.run(  # nosec B603 B607 - argv list, shell=False
            [
                "aws", "cloudformation", "list-stacks",
                *aws.cli_region_args(region),
                "--query",
                "StackSummaries[?StackStatus != 'DELETE_COMPLETE']"
                ".[StackName,StackStatus]",
                "--output", "text",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - must never raise
        return [], f"{type(exc).__name__}: {exc}"

    if proc.returncode != 0:
        return [], (proc.stderr or proc.stdout or "").strip()

    stacks: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].startswith(f"{namespace}-"):
            stacks.append((parts[0], parts[1]))
    return stacks, ""


def render_pointer(
    namespace: str,
    env: str,
    region: str,
    credentials: str,
    stacks: list[tuple[str, str]],
    env_values: dict[str, str] | None = None,
) -> str:
    """The pointer's text. Readable with no credentials configured."""
    env_values = env_values or {}
    lines = [
        f"# Standing resources — run namespace `{namespace}`",
        "",
        "**These resources are BILLABLE and are still deployed.** A passing "
        "integration-test run leaves them standing on purpose, so a maintainer can "
        "open the application in a browser and confirm by eye what the assertions "
        "claim.",
        "",
        "## Remove them",
        "",
        "```bash",
        f"cd {HERE}",
        f"make teardown-namespace NAMESPACE={namespace}",
        "```",
        "",
        f"- namespace: `{namespace}`",
        f"- environment: `{env}`",
        f"- region: `{region}`",
        f"- credentials: `{credentials}`",
        "",
    ]
    if stacks:
        lines += ["## Stacks", ""]
        lines += [f"- `{name}` — {status}" for name, status in stacks]
        lines.append("")
    for key in ("APP_URL", "API_URL", "LOG_BUCKET_NAME", "ECR_REPOSITORY_NAME"):
        if env_values.get(key):
            lines.append(f"- {key}: `{env_values[key]}`")
    if any(env_values.get(k) for k in ("APP_URL", "API_URL")):
        lines.append("")
    return "\n".join(lines) + "\n"


def write_report(
    namespace: str,
    env: str,
    region: str,
    credentials: str,
    stacks: list[tuple[str, str]],
    env_values: dict[str, str] | None = None,
    redact=None,
) -> Path:
    """Write the pointer to a file. FILE FIRST -- see ``report_everywhere``."""
    text = render_pointer(namespace, env, region, credentials, stacks, env_values)
    if redact is not None:
        text = redact(text)
    path = pointer_path(namespace)
    path.write_text(text)
    return path


def report_everywhere(
    namespace: str,
    env: str,
    region: str,
    credentials: str,
    stacks: list[tuple[str, str]],
    env_values: dict[str, str] | None = None,
    redact=None,
) -> Path:
    """Emit the standing-resource report through all three channels, file first.

    Each channel fails differently: a printed report is lost with the terminal, and
    a warning can be suppressed by the test runner's configuration. The file
    survives both, so it is written FIRST — a crash between channels then loses the
    weaker channels rather than the strongest.
    """
    import warnings  # noqa: PLC0415

    path = write_report(
        namespace, env, region, credentials, stacks, env_values, redact=redact
    )
    message = (
        f"{len(stacks)} BILLABLE stack(s) left standing under namespace "
        f"{namespace!r}. Remove with: make teardown-namespace NAMESPACE={namespace} "
        f"(details: {path})"
    )
    print(f"\n{message}\n")
    warnings.warn(message, stacklevel=2)
    return path


def remove_pointer(namespace: str) -> bool:
    """Remove a namespace's pointer. Returns whether a file was removed.

    Callers must call this ONLY for a namespace whose resources were CONFIRMED
    deleted (reference F5).
    """
    path = pointer_path(namespace)
    if path.is_file():
        path.unlink()
        return True
    return False
