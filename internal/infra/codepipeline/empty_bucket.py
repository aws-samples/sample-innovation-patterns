"""Empty the pipeline stack's VERSIONED bucket so ``delete-stack`` can succeed.

WHY THIS IS PYTHON WHEN THE REST OF THE MAKEFILE IS RAW ``aws`` CALLS
--------------------------------------------------------------------
This is the one piece of real logic in the stack's lifecycle. ``aws s3 rm
--recursive`` leaves every noncurrent version and every delete marker behind, and
``delete-stack`` then fails on a bucket the operator believes is empty. Doing it
properly needs pagination over TWO distinct response keys — ``Versions`` and
``DeleteMarkers`` — and batching in pages of up to 1000. A shell one-liner using
``--query`` piped into ``delete-objects`` silently truncates at the first page,
which produces exactly that misleading failure.

WHY IT SHELLS OUT TO ``aws s3api`` INSTEAD OF IMPORTING boto3
-------------------------------------------------------------
``internal/integration-tests/reaper.py`` sets the precedent, and there is a
concrete reason here: this stack's lifecycle must be runnable with a bare
``python3``, which has no boto3. The harness's own dependencies live in a uv
project under ``internal/integration-tests``, which has nothing to do with this
stack — depending on it would make teardown fail with an ``ImportError`` at the
exact moment an operator is trying to delete infrastructure.

Internal maintainer tooling. Not shipped — see ``internal/README.md``.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - runs the AWS CLI with hardcoded argv lists and shell=False
import sys

#: ``delete-objects`` accepts at most 1000 keys per call. Exceeding it is a hard API
#: error, not a silent truncation — but building the batches here is what makes that
#: irrelevant.
DELETE_BATCH_SIZE = 1000


def _aws(args: list[str], *, profile: str | None, region: str | None) -> str:
    """Run one AWS CLI command and return stdout, raising with stderr on failure."""
    argv = ["aws"]
    if profile:
        argv += ["--profile", profile]
    if region:
        argv += ["--region", region]
    argv += args

    proc = subprocess.run(  # nosec B603 B607 - hardcoded argv, shell=False; `aws` from PATH deliberately, since install locations differ across platforms
        argv, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"`{' '.join(argv)}` failed: {(proc.stderr or proc.stdout).strip()}"
        )
    return proc.stdout


def resolve_bucket(stack: str, *, profile: str | None, region: str | None) -> str:
    """Read the bucket name from the stack's own output.

    Resolved from the stack rather than taken as a literal, so this cannot empty the
    wrong bucket because someone mistyped a name next to a ``--force``-shaped
    operation.
    """
    out = _aws(
        [
            "cloudformation",
            "describe-stacks",
            "--stack-name",
            stack,
            "--query",
            "Stacks[0].Outputs[?OutputKey=='SourceBucketName'].OutputValue | [0]",
            "--output",
            "text",
        ],
        profile=profile,
        region=region,
    ).strip()

    if not out or out == "None":
        raise RuntimeError(
            f"stack {stack!r} has no SourceBucketName output — refusing to guess a "
            "bucket name for a delete operation"
        )
    return out


def _iter_pages(bucket: str, *, profile: str | None, region: str | None):
    """Yield each page of ``list-object-versions`` for the whole bucket.

    Paginated by hand via ``--starting-token`` rather than relying on the CLI's own
    pagination, so the page size is ours and every page is observed.
    """
    token: str | None = None
    while True:
        args = [
            "s3api",
            "list-object-versions",
            "--bucket",
            bucket,
            "--max-items",
            str(DELETE_BATCH_SIZE),
            "--output",
            "json",
        ]
        if token:
            args += ["--starting-token", token]

        page = json.loads(_aws(args, profile=profile, region=region) or "{}")
        yield page

        token = page.get("NextToken")
        if not token:
            return


def collect_targets(page: dict) -> list[dict]:
    """Every deletable identifier on one page.

    BOTH keys matter. ``Versions`` holds object versions; ``DeleteMarkers`` holds the
    tombstones left by earlier deletions. A bucket with only delete markers left looks
    empty to ``aws s3 ls`` and still blocks ``delete-stack``.
    """
    targets: list[dict] = []
    for key in ("Versions", "DeleteMarkers"):
        for entry in page.get(key) or []:
            targets.append({"Key": entry["Key"], "VersionId": entry["VersionId"]})
    return targets


def batched(items: list[dict], size: int = DELETE_BATCH_SIZE):
    """Split into API-sized batches. The truncation a shell one-liner does silently."""
    for start in range(0, len(items), size):
        yield items[start : start + size]


def empty_bucket(bucket: str, *, profile: str | None, region: str | None) -> int:
    """Remove every object version and delete marker. Returns the number removed."""
    removed = 0
    for page in _iter_pages(bucket, profile=profile, region=region):
        targets = collect_targets(page)
        if not targets:
            continue
        for batch in batched(targets):
            payload = json.dumps({"Objects": batch, "Quiet": True})
            _aws(
                [
                    "s3api",
                    "delete-objects",
                    "--bucket",
                    bucket,
                    "--delete",
                    payload,
                ],
                profile=profile,
                region=region,
            )
            removed += len(batch)
            print(f"  removed {removed} version(s)/marker(s)...", flush=True)
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Empty the pipeline stack's versioned bucket before delete-stack."
    )
    parser.add_argument("--stack", required=True, help="Pipeline stack name.")
    parser.add_argument("--region", default=None, help="AWS region.")
    parser.add_argument("--profile", default=None, help="AWS profile, if any.")
    parser.add_argument(
        "--bucket",
        default=None,
        help="Override the bucket name instead of reading the stack output. For a "
        "stack that has already been partially deleted.",
    )
    args = parser.parse_args(argv)

    try:
        bucket = args.bucket or resolve_bucket(
            args.stack, profile=args.profile, region=args.region
        )
    except RuntimeError as exc:
        # A stack that is already gone is not a failure: the goal state is "the bucket
        # has nothing in it", and an absent bucket satisfies that.
        print(f"Could not resolve the bucket ({exc}).", file=sys.stderr)
        print("Nothing to empty. Continuing.", file=sys.stderr)
        return 0

    print(f"Emptying s3://{bucket} (every version and delete marker)...")
    try:
        removed = empty_bucket(bucket, profile=args.profile, region=args.region)
    except RuntimeError as exc:
        if "NoSuchBucket" in str(exc):
            print("Bucket is already gone — nothing to empty.")
            return 0
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if removed:
        print(f"Removed {removed} version(s)/marker(s) from s3://{bucket}.")
    else:
        print(f"s3://{bucket} was already empty.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
