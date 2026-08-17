"""Remove everything one integration-test run created.

The generated aggregates are **invoked, not replaced**: ``scripts/deploy.mk``'s
``teardown`` and ``scripts/prepare.mk``'s ``teardown-prepare`` already encode
reverse deployment order and already wait for completion. Reimplementing that here
would duplicate a contract this harness does not own, and would drift the day a
tier is added.

What the reaper adds is the three steps IPA's own skills deliberately refuse to
take:

1. **Empty the versioned buckets** — including every non-current version and every
   delete marker. See ``purge_versions`` for why this is the normal path here
   rather than a fallback.
2. **Empty the ECR registry** — ``DeleteRepository`` fails on a repository holding
   images.
3. **Delete ``{ns}-{env}-security``** — ``/ipa-destroy`` leaves it standing.

The log bucket is emptied **twice**: once before the aggregates run and once again
immediately before its own tier goes. ``MAKEFILE_TEMPLATES.md`` states it keeps
receiving CloudFront logs until the frontend stack is torn down, so a single
pre-pass races against delivery that continues after it.
"""

from __future__ import annotations

import subprocess  # nosec B404 - argv lists only, shell=False; see .ash/ash.yaml
from dataclasses import dataclass, field
from pathlib import Path

#: `aws s3 rm --recursive` is the exact command the skill's own recovery guidance
#: names, and it handles pagination and batching itself.
_S3_RM_TIMEOUT = 900
_ECR_TIMEOUT = 300
#: `delete-objects` accepts at most 1000 keys per call, so the version sweep pages
#: at that size. The page cap is a runaway guard, not a tuned figure: a log bucket
#: that has accumulated 50k versions is a different problem from the one this
#: module solves, and it should be reported rather than looped over silently.
_S3_VERSION_PAGE_SIZE = 1000
_S3_VERSION_MAX_PAGES = 50
#: Teardown waits for stack deletion, and CloudFront distribution deletion is slow.
#: Generous rather than tuned — an aggregate that times out leaves a half-deleted
#: stack, which is worse than waiting.
_MAKE_TIMEOUT = 3600


@dataclass
class Step:
    """One reaping action and what actually happened to it.

    ``ok`` records the STATE REACHED, never that a command was issued. The
    reference harness's most expensive bug was a test asserting that
    ``aws s3 rm`` *ran* — which is exactly the assumption that failed, so it
    passed against two broken runs.
    """

    name: str
    ok: bool
    detail: str = ""


@dataclass
class Report:
    steps: list[Step] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> Step:
        step = Step(name=name, ok=ok, detail=detail)
        self.steps.append(step)
        return step

    @property
    def ok(self) -> bool:
        return all(s.ok for s in self.steps)

    def render(self) -> str:
        return "\n".join(
            f"  {'ok  ' if s.ok else 'FAIL'} {s.name}"
            + (f" -- {s.detail}" if s.detail else "")
            for s in self.steps
        )


def _run(argv: list[str], timeout: int, cwd: Path | None = None) -> tuple[bool, str]:
    """Run ``argv`` with ``shell=False``; never raises."""
    try:
        proc = subprocess.run(  # nosec B603 B607 - argv list, shell=False
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return False, f"{argv[0]}: not found on PATH"
    except subprocess.TimeoutExpired:
        return False, f"{argv[0]}: timed out after {timeout}s"
    except OSError as exc:  # pragma: no cover - defensive
        return False, f"{argv[0]}: {exc}"
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "").strip()
    return True, (proc.stdout or "").strip()


# --------------------------------------------------------------------------- #
# The version purge -- the step `aws s3 rm --recursive` cannot do
# --------------------------------------------------------------------------- #


def purge_versions(
    bucket: str,
    profile: str,
    region: str,
    runner=_run,
) -> tuple[bool, str]:
    """Delete every object VERSION and every DELETE MARKER in ``bucket``.

    **This is the step ``aws s3 rm --recursive`` cannot do, and the reason this
    function exists.** On a versioned bucket ``s3 rm`` deletes only the *current*
    version of each key: it writes a delete marker and leaves the previous version
    in place. So ``aws s3 ls`` afterwards shows an empty bucket while S3 still
    holds both the non-current version and the marker — and CloudFormation's
    ``DeleteBucket`` fails with *"The bucket you tried to delete is not empty. You
    must delete all versions in the bucket."*

    That combination is what makes the bug expensive: the emptying step reports
    success, the listing corroborates it, and the failure surfaces minutes later
    inside a generated teardown aggregate as a stack that will not delete. Both
    buckets IPA creates come from templates that enable versioning, so this sweep
    is the **normal path** here, not a fallback.

    A **failed listing must not report the bucket as emptied.** That is the
    reference's most expensive class of bug in miniature: a report that a command
    ran standing in for a state having been reached.

    Emptying an unversioned or already-empty bucket lists nothing and deletes
    nothing, so this is a no-op rather than an error in that case.
    """
    removed = 0
    for page in range(_S3_VERSION_MAX_PAGES):
        ok, out = runner(
            [
                "aws", "s3api", "list-object-versions",
                "--bucket", bucket,
                "--max-items", str(_S3_VERSION_PAGE_SIZE),
                "--profile", profile,
                "--region", region,
                "--output", "json",
            ],
            _S3_RM_TIMEOUT,
        )
        if not ok:
            # NOT "emptied". A listing failure is unknown state, not success.
            return False, (
                f"could not list versions after removing {removed} "
                f"(bucket may still hold versions): {out}"
            )

        import json  # noqa: PLC0415 - kept local so the module imports without it

        try:
            listing = json.loads(out) if out.strip() else {}
        except json.JSONDecodeError as exc:
            return False, f"could not parse version listing: {exc}"

        # BOTH lists must be drained. Draining only Versions leaves the delete
        # markers, and DeleteBucket refuses on markers alone.
        objects = [
            {"Key": v["Key"], "VersionId": v["VersionId"]}
            for v in (listing.get("Versions") or [])
        ] + [
            {"Key": m["Key"], "VersionId": m["VersionId"]}
            for m in (listing.get("DeleteMarkers") or [])
        ]
        if not objects:
            return True, f"emptied ({removed} versions/markers removed)"

        ok, out = runner(
            [
                "aws", "s3api", "delete-objects",
                "--bucket", bucket,
                "--delete", json.dumps({"Objects": objects, "Quiet": True}),
                "--profile", profile,
                "--region", region,
            ],
            _S3_RM_TIMEOUT,
        )
        if not ok:
            return False, f"delete-objects failed after removing {removed}: {out}"
        removed += len(objects)

    return False, (
        f"still not empty after {_S3_VERSION_MAX_PAGES} pages ({removed} removed); "
        "a bucket this large is a different problem -- reporting rather than looping"
    )


def empty_bucket(bucket: str, profile: str, region: str, runner=_run) -> tuple[bool, str]:
    """Empty a bucket: the fast recursive delete, then the version sweep.

    The recursive delete runs first because it is fast and handles the common
    case. The version sweep then runs **unconditionally**, because on a versioned
    bucket the recursive delete leaves the bucket un-deletable while making it look
    empty.
    """
    rm_ok, rm_detail = runner(
        [
            "aws", "s3", "rm", f"s3://{bucket}", "--recursive",
            "--profile", profile, "--region", region,
        ],
        _S3_RM_TIMEOUT,
    )
    purge_ok, purge_detail = purge_versions(bucket, profile, region, runner=runner)
    # The purge is authoritative: it is the step that determines whether
    # DeleteBucket will succeed.
    detail = f"rm={'ok' if rm_ok else rm_detail or 'failed'}; purge={purge_detail}"
    return purge_ok, detail


def empty_ecr(repository: str, profile: str, region: str, runner=_run) -> tuple[bool, str]:
    """Delete every image in an ECR repository; DeleteRepository fails otherwise."""
    ok, out = runner(
        [
            "aws", "ecr", "list-images",
            "--repository-name", repository,
            "--query", "imageIds[*]",
            "--profile", profile, "--region", region,
            "--output", "json",
        ],
        _ECR_TIMEOUT,
    )
    if not ok:
        return False, f"could not list images: {out}"

    import json  # noqa: PLC0415

    try:
        image_ids = json.loads(out) if out.strip() else []
    except json.JSONDecodeError as exc:
        return False, f"could not parse image listing: {exc}"
    if not image_ids:
        return True, "already empty"

    ok, out = runner(
        [
            "aws", "ecr", "batch-delete-image",
            "--repository-name", repository,
            "--image-ids", json.dumps(image_ids),
            "--profile", profile, "--region", region,
        ],
        _ECR_TIMEOUT,
    )
    return (True, f"deleted {len(image_ids)} image(s)") if ok else (False, out)


# --------------------------------------------------------------------------- #
# The reaper
# --------------------------------------------------------------------------- #


class ReaperRefused(RuntimeError):
    """Raised when the reaper is pointed at a project it cannot describe."""


def assert_reapable(project: Path) -> None:
    """Refuse to proceed without the generated artifacts a completed run produces.

    Those artifacts encode the reverse ordering and the deletion waits. Without
    them the reaper would be improvising an order against infrastructure it cannot
    describe.
    """
    deploy_mk = Path(project) / "scripts" / "deploy.mk"
    if not deploy_mk.is_file():
        raise ReaperRefused(
            f"refusing to reap: {deploy_mk} is absent, so the reverse teardown "
            "order and the deletion waits are unknown. Point the reaper at the "
            "temp project the run composed, or use sweep.py to remove stacks by "
            "namespace."
        )


def reap(
    project: Path,
    namespace: str,
    env: str,
    profile: str,
    region: str,
    log_bucket: str | None = None,
    site_bucket: str | None = None,
    ecr_repository: str | None = None,
    runner=_run,
) -> Report:
    """Remove one run's infrastructure. Never raises except ``ReaperRefused``."""
    assert_reapable(project)
    project = Path(project)
    report = Report()

    # 1. Empty the buckets and the registry BEFORE the aggregates run, because
    #    the stacks that own them will not delete while they hold objects.
    #    log_bucket comes from .env's LOG_BUCKET_NAME -- the reference needed a
    #    name-resolution special case here and IPA does not.
    for label, bucket in (("log bucket", log_bucket), ("site bucket", site_bucket)):
        if bucket:
            ok, detail = empty_bucket(bucket, profile, region, runner=runner)
            report.add(f"empty {label} {bucket}", ok, detail)

    if ecr_repository:
        ok, detail = empty_ecr(ecr_repository, profile, region, runner=runner)
        report.add(f"empty ecr {ecr_repository}", ok, detail)

    # 2. The generated aggregates, which own the per-tier ordering and the waits.
    ok, detail = runner(
        ["make", "-f", "scripts/deploy.mk", "teardown"], _MAKE_TIMEOUT, project
    )
    report.add("make -f scripts/deploy.mk teardown", ok, detail if not ok else "")

    # 3. The log bucket AGAIN: MAKEFILE_TEMPLATES.md states it keeps receiving
    #    CloudFront logs until the frontend stack is torn down, so the pre-pass
    #    above raced against delivery that continued after it.
    if log_bucket:
        ok, detail = empty_bucket(log_bucket, profile, region, runner=runner)
        report.add(f"re-empty log bucket {log_bucket}", ok, detail)

    ok, detail = runner(
        ["make", "-f", "scripts/prepare.mk", "teardown-prepare"],
        _MAKE_TIMEOUT,
        project,
    )
    report.add(
        "make -f scripts/prepare.mk teardown-prepare", ok, detail if not ok else ""
    )

    # 4. The security stack, which /ipa-destroy leaves standing.
    security_stack = f"{namespace}-{env}-security"
    ok, detail = runner(
        [
            "aws", "cloudformation", "delete-stack",
            "--stack-name", security_stack,
            "--profile", profile, "--region", region,
        ],
        _MAKE_TIMEOUT,
    )
    if ok:
        ok, detail = runner(
            [
                "aws", "cloudformation", "wait", "stack-delete-complete",
                "--stack-name", security_stack,
                "--profile", profile, "--region", region,
            ],
            _MAKE_TIMEOUT,
        )
    report.add(f"delete-stack {security_stack}", ok, detail if not ok else "")

    return report
