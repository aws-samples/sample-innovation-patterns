"""Find and remove integration-test stacks across runs, scoped by namespace.

Namespaces are unique per run, so a forgotten run leaves billable infrastructure
that nothing but a prefix sweep can find. That is why this module exists even
though only one test needs it.

Two properties are the dangerous ones, and both are designed to be provable
offline:

*   **``select_namespaces`` is a pure function** over an already-grouped listing,
    not a narrowing of the prefix passed to the API. That is what makes "what gets
    deleted" testable without deleting anything.
*   **Nothing may tie with the ``logs`` rank.** Python's sort is stable, so two
    entries sharing a rank keep input order — and the log bucket would then delete
    before a dependent tier on some runs and after it on others, depending on how
    the stack listing happened to come back.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - argv lists only, shell=False; see .ash/ash.yaml
import sys
from pathlib import Path

from harness import aws, standing

#: Teardown order for IPA's tiers. `logs` is deliberately ABSENT -- see below.
TIER_ORDER = ("frontend", "backend", "queue", "cognito", "ecr", "security")

#: Ranks for the two cases outside TIER_ORDER.
#:
#: An unknown tier sorts after every known one but strictly BEFORE `logs`, so a
#: tier added later is removed before the log bucket.
#:
#: These MUST NOT collide. Appending "logs" to TIER_ORDER is the tempting form and
#: is exactly what makes an unknown tier tie with it: Python's sort is stable, so a
#: tie keeps input order, which for `logs` means the log bucket sometimes going
#: first depending on how the stack listing came back. MAKEFILE_TEMPLATES.md states
#: the log bucket keeps receiving CloudFront logs until the frontend stack is torn
#: down, so removing it earlier deletes a bucket that is still being written to.
UNKNOWN_RANK = len(TIER_ORDER)
LOGS_RANK = len(TIER_ORDER) + 1


def tier_of(stack_name: str) -> str:
    """The tier suffix of a stack name, or the trailing segment if unrecognised."""
    for suffix in (*TIER_ORDER, "logs"):
        if stack_name.endswith(f"-{suffix}"):
            return suffix
    return stack_name.rsplit("-", 1)[-1] if "-" in stack_name else stack_name


def tier_rank(stack_name: str) -> int:
    """Sort key placing a stack in the documented teardown order."""
    if stack_name.endswith("-logs"):
        return LOGS_RANK
    for index, suffix in enumerate(TIER_ORDER):
        if stack_name.endswith(f"-{suffix}"):
            return index
    return UNKNOWN_RANK


def teardown_order(stacks: list[str]) -> list[str]:
    """Stacks in the order they must be removed."""
    return sorted(stacks, key=tier_rank)


def select_namespaces(
    grouped: dict[str, list[str]], only: str | None
) -> dict[str, list[str]]:
    """Narrow a grouped stack listing to one namespace, or pass it through.

    A **pure function** over the ALREADY-GROUPED listing rather than a narrowing of
    the prefix passed to the API. Two reasons, both load-bearing:

    1. It makes the most dangerous behaviour in the system — what gets deleted —
       testable with no credentials and nothing deleted.
    2. An unmatched namespace selects **nothing**, and a caller can tell the
       difference between "nothing matched" and "everything matched", which a
       prefix narrowed at the API cannot express.

    A missing or empty ``only`` passes the listing through unchanged. Callers that
    delete MUST refuse an empty namespace before reaching here — see ``main``.
    """
    if not only:
        return dict(grouped)
    return {ns: stacks for ns, stacks in grouped.items() if ns == only}


def _run(argv: list[str], timeout: int = 300) -> tuple[bool, str]:
    try:
        proc = subprocess.run(  # nosec B603 B607 - argv list, shell=False
            argv, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return False, str(exc)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "").strip()
    return True, (proc.stdout or "").strip()


def group_by_namespace(stack_names: list[str], env: str = "dev") -> dict[str, list[str]]:
    """Group stack names by the namespace segment of ``{ns}-{env}-{tier}``."""
    grouped: dict[str, list[str]] = {}
    marker = f"-{env}-"
    for name in stack_names:
        if marker not in name:
            continue
        ns = name.split(marker, 1)[0]
        grouped.setdefault(ns, []).append(name)
    return grouped


def list_it_stacks(region: str = aws.REGION, prefix: str = "it") -> tuple[list[str], str]:
    """Every live stack whose name starts with the harness's namespace prefix."""
    ok, out = _run(
        [
            "aws", "cloudformation", "list-stacks",
            *aws.cli_region_args(region),
            "--query",
            "StackSummaries[?StackStatus != 'DELETE_COMPLETE'].StackName",
            "--output", "text",
        ]
    )
    if not ok:
        return [], out
    names = [n for n in out.split() if n.startswith(prefix)]
    return names, ""


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def cmd_list(region: str = aws.REGION) -> int:
    names, error = list_it_stacks(region)
    if error:
        print(f"could not list stacks: {error}", file=sys.stderr)
        return 1
    grouped = group_by_namespace(names)
    if not grouped:
        print("No integration-test stacks found.")
        return 0
    for ns, stacks in sorted(grouped.items()):
        print(f"\n  {ns}:")
        for name in teardown_order(stacks):
            print(f"    - {name}")
    total = sum(len(v) for v in grouped.values())
    print(f"\n{total} stack(s) across {len(grouped)} run(s). These are BILLABLE.")
    print("Remove one run with:  make teardown-namespace NAMESPACE=<namespace>")
    return 0


def cmd_teardown(region: str, namespace: str | None) -> int:
    # Opt-in one of two. The other is the `teardown` pytest marker.
    if os.environ.get("IPA_IT_TEARDOWN") != "1":
        print(
            "Refusing to delete anything: IPA_IT_TEARDOWN=1 is not set.\n"
            "Teardown requires TWO independent opt-ins, because one is satisfiable "
            "by accident -- a pipeline-level variable applies to every phase of "
            "every build.",
            file=sys.stderr,
        )
        return 2

    # An empty namespace is NEVER "every run". That is the unbounded failure mode:
    # it would delete other runs' infrastructure, and possibly infrastructure that
    # is not a test run at all.
    if not namespace:
        print(
            "Refusing to delete anything: no NAMESPACE given. An empty namespace is "
            "not treated as 'every run'.",
            file=sys.stderr,
        )
        return 2

    names, error = list_it_stacks(region)
    if error:
        print(f"could not list stacks: {error}", file=sys.stderr)
        return 1

    selected = select_namespaces(group_by_namespace(names), namespace)
    if not selected:
        # "Nothing matched" is reported as such, not as success over an empty set.
        print(
            f"No stacks found under namespace {namespace!r}. Nothing was deleted.",
            file=sys.stderr,
        )
        return 1

    all_confirmed = True
    for ns, stacks in selected.items():
        print(f"\nTearing down {ns} ({len(stacks)} stack(s))")
        confirmed = True
        for name in teardown_order(stacks):
            ok, detail = _run(
                [
                    "aws", "cloudformation", "delete-stack",
                    "--stack-name", name,
                    *aws.cli_region_args(region),
                ]
            )
            if ok:
                ok, detail = _run(
                    [
                        "aws", "cloudformation", "wait", "stack-delete-complete",
                        "--stack-name", name,
                        *aws.cli_region_args(region),
                    ],
                    timeout=3600,
                )
            print(f"  {'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f" -- {detail}"))
            confirmed = confirmed and ok

        # The pointer is removed ONLY for a namespace whose stacks were CONFIRMED
        # deleted (reference F5). A pointer surviving a successful teardown errs
        # safe but teaches a reader to distrust the next pointer, which may be
        # true; a pointer removed after a FAILED teardown loses the only record of
        # what is still costing money.
        if confirmed:
            removed = standing.remove_pointer(ns)
            print(f"  {'removed' if removed else 'no'} standing-resources pointer for {ns}")
        else:
            print(
                f"  KEEPING standing-resources pointer for {ns}: teardown was partial"
            )
        all_confirmed = all_confirmed and confirmed

    return 0 if all_confirmed else 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    command = argv[0] if argv else "list"
    region = aws.REGION
    namespace = os.environ.get("NAMESPACE") or (argv[1] if len(argv) > 1 else None)

    if command == "list":
        return cmd_list(region)
    if command == "teardown":
        return cmd_teardown(region, namespace)
    print(f"unknown command {command!r}; expected 'list' or 'teardown'", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
