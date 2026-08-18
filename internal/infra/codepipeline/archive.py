"""Build the source archive the pipeline runs, from the repository's WORKING TREE.

WHAT GOES IN, AND WHY IT IS NOT ``git archive``
----------------------------------------------
Two sets, unioned:

1. Every non-ignored file — ``git ls-files`` plus ``git ls-files --others
   --exclude-standard``. This is *exactly* the set
   ``internal/integration-tests/workspace.py`` copies into the temp project, so what
   the pipeline tests is what a local run tests. Ignored files are excluded, which is
   what keeps ``.env`` and the generated ``scripts/*.mk`` out — and their absence is
   what keeps ``/ipa-init`` on its first-run path.
2. **The ``.git`` directory.** ``git archive HEAD`` would give neither: it archives
   the COMMIT, so uncommitted edits vanish, and it carries no git metadata at all.
   ``workspace.py`` shells out to ``git ls-files``, ``git rev-parse HEAD`` and ``git
   status --porcelain`` with ``check=True``, so an archive without ``.git`` does not
   fail here with a cause — it fails inside a pytest fixture with a
   ``CalledProcessError``.

The result is that a DIRTY tree stays dirty in the archive and is reported as such by
the build. That is deliberate: testing an uncommitted skill edit remotely is a real
use, and the honest failure mode is a loud warning, not a silently substituted commit.

WHY A WORKTREE IS REFUSED
-------------------------
In a linked worktree ``.git`` is a FILE containing a ``gitdir:`` pointer to the parent
repository, not a directory. Zipping that pointer produces an archive whose git
commands all fail on a path that does not exist in the build container. Refused up
front, by name, rather than diagnosed from CodeBuild logs.

Internal maintainer tooling. Not shipped — see ``internal/README.md``.
"""

from __future__ import annotations

import argparse
import os
import subprocess  # nosec B404 - argv lists only, shell=False
import sys
import zipfile
from pathlib import Path

#: Resolved from this file, never from the caller's cwd:
#: internal/infra/codepipeline/archive.py -> repository root.
REPO_ROOT = Path(__file__).resolve().parents[3]


def _git(repo: Path, *args: str) -> list[str]:
    """Run git with an argv list and return its non-empty stdout lines."""
    proc = subprocess.run(  # nosec B603 B607 - argv list, shell=False
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def tracked_and_untracked(repo: Path) -> list[str]:
    """Every file in the working tree that is not ignored.

    The same union ``workspace.tracked_and_untracked`` builds. Kept as its own
    implementation rather than importing that module: this script must run under a
    bare ``python3`` from any directory, and importing the harness would drag in its
    uv project.
    """
    tracked = _git(repo, "ls-files")
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked) | set(untracked))


def assert_real_git_dir(repo: Path) -> None:
    """Refuse a linked worktree, which has a ``.git`` FILE rather than a directory."""
    git_path = repo / ".git"
    if git_path.is_dir():
        return
    if git_path.is_file():
        raise SystemExit(
            f"{repo} is a linked git worktree ({git_path} is a file, not a "
            "directory).\n"
            "  Its .git pointer names a path that will not exist in the build "
            "container, so every git call the harness makes would fail there.\n"
            "  Build the archive from the main checkout instead, or pass --repo "
            "pointing at it."
        )
    raise SystemExit(f"{repo} is not a git repository: no {git_path}")


def _git_dir_files(repo: Path) -> list[str]:
    """Every file under ``.git``, as repo-relative POSIX paths."""
    rels: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(repo / ".git"):
        for name in filenames:
            full = Path(dirpath) / name
            # Symlinks and sockets inside .git are not portable and not needed.
            if full.is_file() and not full.is_symlink():
                rels.append(full.relative_to(repo).as_posix())
    return sorted(rels)


def _add(zf: zipfile.ZipFile, repo: Path, rel: str) -> bool:
    """Add one file, preserving its permission bits. Returns whether it was added."""
    src = repo / rel
    # ls-files can name a path that no longer exists (a staged deletion).
    if not src.is_file():
        return False
    info = zipfile.ZipInfo.from_file(src, arcname=rel)
    # from_file already carries the mode in external_attr, which is what preserves
    # the executable bit through CodePipeline's unzip. Losing it would surface as a
    # "permission denied" on a shell script during the run, not here.
    zf.writestr(info, src.read_bytes())
    return True


def build(repo: Path, out: Path) -> tuple[int, bool, str]:
    """Write the archive. Returns ``(file_count, dirty, commit)``."""
    assert_real_git_dir(repo)

    commit = _git(repo, "rev-parse", "HEAD")[0]
    dirty = bool(_git(repo, "status", "--porcelain"))

    rels = tracked_and_untracked(repo)
    git_rels = _git_dir_files(repo)

    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in rels:
            count += _add(zf, repo, rel)
        for rel in git_rels:
            _add(zf, repo, rel)

    return count, dirty, commit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the integration-test pipeline's source archive."
    )
    parser.add_argument(
        "--repo",
        default=str(REPO_ROOT),
        help="Repository to archive. Defaults to the checkout this file lives in.",
    )
    parser.add_argument("--out", required=True, help="Path of the zip to write.")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve()

    count, dirty, commit = build(repo, out)
    size_mb = out.stat().st_size / (1024 * 1024)

    print(f"archive:  {out} ({size_mb:.1f} MiB)")
    print(f"repo:     {repo}")
    print(f"commit:   {commit}{' (DIRTY)' if dirty else ''}")
    print(f"files:    {count} non-ignored, plus .git")
    if dirty:
        # Printed, not fatal. A dirty archive is a legitimate thing to run; a dirty
        # archive nobody noticed is not.
        print(
            "\nWARNING: the working tree has uncommitted changes. This archive "
            "contains them,\n"
            "         so the commit above does not fully describe what will run.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
