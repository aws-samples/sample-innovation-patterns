"""Build the temp project the IPA lifecycle skills are driven against.

The temp project is a copy of the repository's **working tree**, not of any commit.
``git archive HEAD`` archives the COMMIT, so a maintainer testing an uncommitted
skill edit would get a green run describing a tree nobody has — which is worse
than a red run, because it is believed.

Three properties are asserted inside ``build()`` rather than only in the test
module, so a caller that skips the tests cannot produce a subtly wrong temp
project:

1. **No ``.env`` and no ``scripts/*.mk``.** Both are git-ignored
   (``.gitignore:23``, ``scripts/.gitignore``), so a tracked-plus-untracked copy
   naturally has neither. It is asserted anyway because the absence is
   load-bearing and the ignore rules are editable: it is the precondition that
   keeps ``/ipa-init`` on its first-run path. Its re-initialization branch asks a
   plain-text *"Which values would you like to change?"* that no permission hook
   and no tool callback can intercept, so a run starting from a configured project
   cannot be driven unattended at all.
2. **Every artifact a later phase depends on is present.** A silently incomplete
   copy fails much later, inside a container build, with an error naming a missing
   file rather than a missing copy.
3. **The destination is outside the repository.** A nested temp project is picked
   up by ``git status``, by ``./lint`` and by ASH, so a run would report findings
   against a copy of the tree rather than against the tree.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - argv lists only, shell=False; see .ash/ash.yaml
import tempfile
from dataclasses import dataclass
from pathlib import Path

#: Resolved from this file, never from the caller's cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]

#: Each of these is something a later phase depends on. Their presence is asserted
#: at build time so a truncated copy fails here rather than inside a build.
REQUIRED_ARTIFACTS = (
    ".claude/skills/ipa-stack-backend/SKILL.md",
    "infra/cfn/queue/queue.yml",
    "infra/scripts/docker.mk",
    "web-client/package-lock.json",
    "app-lib/pyproject.toml",
)


@dataclass(frozen=True)
class Source:
    """What the temp project was built from.

    Returned as data rather than logged, so the driver can put both fields in the
    transcript: a run's result must name the tree it ran against, and for a dirty
    tree the commit alone is a false description.
    """

    commit: str
    dirty: bool
    root: Path
    file_count: int

    def describe(self) -> str:
        return (
            f"{self.commit[:12]}{'-dirty' if self.dirty else ''} "
            f"({self.file_count} files) -> {self.root}"
        )


def _git(repo: Path, *args: str) -> list[str]:
    """Run git with an argv list and return its stdout lines."""
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

    The union is the right set precisely BECAUSE it excludes ignored files: that
    is what makes the absence of ``.env`` and ``scripts/*.mk`` a property of the
    copy mechanism rather than a step someone could forget.
    """
    tracked = _git(repo, "ls-files")
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked) | set(untracked))


def is_dirty(repo: Path) -> bool:
    return bool(_git(repo, "status", "--porcelain"))


def head_commit(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD")[0]


def _copy_from_working_tree(src: Path, dest: Path) -> None:
    """Copy one file's CONTENTS from the working tree, preserving the exec bit."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    shutil.copymode(src, dest)


#: Generated Makefiles whose presence puts a lifecycle skill onto a branch the
#: harness cannot drive. Deliberately NOT "any scripts/*.mk" -- see below.
#:
#: `scripts/test.mk` is TRACKED in this repository (`git ls-files scripts/`), even
#: though `scripts/.gitignore` lists `*.mk`: git's ignore rules do not apply to a
#: file that is already tracked. So a working-tree copy DOES carry one generated
#: Makefile, and a blanket `*.mk` assertion fails on every healthy build.
#:
#: Narrowing to the gating artifacts is correct rather than merely convenient:
#:   - `.env` is what sends `/ipa-init` into its re-initialization branch, whose
#:     plain-text "Which values would you like to change?" no hook can intercept.
#:   - `scripts/deploy.mk` is what `/ipa-compose` Step 0.3 checks to choose its
#:     idempotent-refresh mode (`ipa-compose/SKILL.md:57`).
#: `test.mk` gates neither, so its presence changes no skill's path.
GATING_MAKEFILES = ("deploy.mk", "prepare.mk", "build.mk", "env.mk", "post-deploy.mk")


def assert_pristine(dest: Path) -> None:
    """No ``.env``, and none of the generated Makefiles that gate a skill branch."""
    env_file = dest / ".env"
    if env_file.exists():
        raise AssertionError(
            f"temp project must not contain .env (found {env_file}); "
            "its presence sends /ipa-init into its re-initialization branch, "
            "whose plain-text prompt no hook can intercept"
        )
    leaked = sorted(
        name for name in GATING_MAKEFILES if (dest / "scripts" / name).exists()
    )
    if leaked:
        raise AssertionError(
            f"temp project must not contain gating generated Makefiles (found "
            f"{leaked} in {dest / 'scripts'}); /ipa-compose must generate them "
            "during the run, and their presence selects its idempotent-refresh mode"
        )


def assert_required_artifacts(dest: Path) -> None:
    """Every artifact a later phase depends on is present."""
    missing = [rel for rel in REQUIRED_ARTIFACTS if not (dest / rel).exists()]
    if missing:
        raise AssertionError(
            f"temp project is missing artifacts a later phase depends on: {missing}"
        )


def assert_outside_repo(dest: Path, repo: Path) -> None:
    """The temp project must not be nested under the repository."""
    if dest.resolve().is_relative_to(repo.resolve()):
        raise AssertionError(
            f"temp project must live outside the repository, got {dest} "
            f"under {repo}; a nested copy is picked up by git status, ./lint and ASH"
        )


def build(dest: Path, repo: Path = REPO_ROOT) -> Source:
    """Copy the repository's working tree into ``dest`` and assert it is usable."""
    dest = Path(dest)
    repo = Path(repo)

    # Asserted BEFORE copying anything, so a bad destination costs nothing.
    assert_outside_repo(dest, repo)

    rels = tracked_and_untracked(repo)
    for rel in rels:
        src = repo / rel
        # ls-files can name a path that no longer exists (a staged deletion).
        if src.is_file():
            _copy_from_working_tree(src, dest / rel)

    assert_pristine(dest)
    assert_required_artifacts(dest)

    return Source(
        commit=head_commit(repo),
        dirty=is_dirty(repo),
        root=dest,
        file_count=len(rels),
    )


def build_temp(repo: Path = REPO_ROOT, prefix: str = "ipa-it-") -> Source:
    """Build into a fresh temp directory outside the repository."""
    dest = Path(tempfile.mkdtemp(prefix=prefix))
    return build(dest, repo)


def resolve_aws_profile() -> str | None:
    """The profile the harness should use, from its own variable or the ambient one."""
    return os.environ.get("IPA_IT_PROFILE") or os.environ.get("AWS_PROFILE") or None
