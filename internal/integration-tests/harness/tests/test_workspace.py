"""Offline tests for temp-project construction.

No AWS credentials, no agent. Each test pins a failure that would otherwise
surface many minutes into a paid run.
"""

from __future__ import annotations

import subprocess  # nosec B404 - argv lists only, shell=False
from pathlib import Path

import pytest

from harness import workspace


def _git(repo: Path, *args: str) -> None:
    subprocess.run(  # nosec B603 B607 - argv list, shell=False
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """A miniature repository carrying every artifact ``build()`` requires."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "T")

    for rel in workspace.REQUIRED_ARTIFACTS:
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"committed content of {rel}\n")

    # Mirror the real repository's ignore rules: .env and scripts/*.mk are ignored.
    (repo / ".gitignore").write_text(".env\n")
    (repo / "scripts").mkdir(exist_ok=True)
    (repo / "scripts" / ".gitignore").write_text("*.mk\n")

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")
    return repo


def test_build_produces_every_required_artifact(fake_repo: Path, tmp_path: Path):
    src = workspace.build(tmp_path / "out", repo=fake_repo)
    for rel in workspace.REQUIRED_ARTIFACTS:
        assert (src.root / rel).is_file(), rel


def test_build_reflects_the_working_tree_not_the_commit(fake_repo: Path, tmp_path: Path):
    """The single most important property of this module.

    ``git archive HEAD`` would archive the COMMIT, so a maintainer testing an
    uncommitted skill edit would get a green run describing a tree nobody has.
    """
    edited = fake_repo / ".claude/skills/ipa-stack-backend/SKILL.md"
    edited.write_text("UNCOMMITTED EDIT under test\n")

    src = workspace.build(tmp_path / "out", repo=fake_repo)

    copied = (src.root / ".claude/skills/ipa-stack-backend/SKILL.md").read_text()
    assert copied == "UNCOMMITTED EDIT under test\n"
    assert "committed content" not in copied


def test_build_includes_an_untracked_file(fake_repo: Path, tmp_path: Path):
    (fake_repo / "infra/cfn/newtier").mkdir(parents=True)
    (fake_repo / "infra/cfn/newtier/newtier.yml").write_text("never committed\n")

    src = workspace.build(tmp_path / "out", repo=fake_repo)

    assert (src.root / "infra/cfn/newtier/newtier.yml").is_file()


def test_build_excludes_an_ignored_file(fake_repo: Path, tmp_path: Path):
    (fake_repo / ".env").write_text("APP_NAMESPACE=leaked\n")

    src = workspace.build(tmp_path / "out", repo=fake_repo)

    assert not (src.root / ".env").exists()


def test_build_records_the_commit_and_the_dirty_flag(fake_repo: Path, tmp_path: Path):
    clean = workspace.build(tmp_path / "clean", repo=fake_repo)
    assert len(clean.commit) == 40
    assert clean.dirty is False

    (fake_repo / "app-lib/pyproject.toml").write_text("dirtied\n")
    dirty = workspace.build(tmp_path / "dirty", repo=fake_repo)
    assert dirty.dirty is True
    assert "dirty" in dirty.describe()


def test_build_refuses_a_destination_inside_the_repository(fake_repo: Path):
    """A nested temp project is picked up by git status, ./lint and ASH."""
    with pytest.raises(AssertionError, match="outside the repository"):
        workspace.build(fake_repo / "nested" / "out", repo=fake_repo)


def test_build_refuses_when_the_copy_would_contain_env(fake_repo: Path, tmp_path: Path):
    """The precondition keeping /ipa-init out of its uninterceptable branch."""
    # Force .env to be TRACKED, so the copy mechanism would carry it.
    (fake_repo / ".gitignore").write_text("")
    (fake_repo / ".env").write_text("APP_NAMESPACE=leaked\n")
    _git(fake_repo, "add", "-A")
    _git(fake_repo, "commit", "-q", "-m", "track env")

    with pytest.raises(AssertionError, match=r"must not contain \.env"):
        workspace.build(tmp_path / "out", repo=fake_repo)


def test_build_refuses_when_the_copy_would_contain_a_gating_makefile(
    fake_repo: Path, tmp_path: Path
):
    (fake_repo / "scripts" / ".gitignore").write_text("")
    (fake_repo / "scripts" / "deploy.mk").write_text("deploy:\n\t@true\n")
    _git(fake_repo, "add", "-A")
    _git(fake_repo, "commit", "-q", "-m", "track mk")

    with pytest.raises(AssertionError, match="gating generated Makefiles"):
        workspace.build(tmp_path / "out", repo=fake_repo)


def test_a_tracked_test_mk_is_tolerated(fake_repo: Path, tmp_path: Path):
    """`scripts/test.mk` is TRACKED in this repository despite `scripts/.gitignore`
    listing `*.mk` — git's ignore rules do not apply to an already-tracked file.

    So a working-tree copy carries it, and it must NOT fail the pristine check: it
    gates neither `/ipa-init`'s re-initialization branch nor `/ipa-compose`'s
    idempotent-refresh mode.
    """
    (fake_repo / "scripts" / ".gitignore").write_text("")
    (fake_repo / "scripts" / "test.mk").write_text("test:\n\t@true\n")
    _git(fake_repo, "add", "-A")
    _git(fake_repo, "commit", "-q", "-m", "track test.mk")

    src = workspace.build(tmp_path / "out", repo=fake_repo)

    assert (src.root / "scripts" / "test.mk").is_file()


def test_test_mk_is_not_in_the_gating_set():
    assert "test.mk" not in workspace.GATING_MAKEFILES
    assert "deploy.mk" in workspace.GATING_MAKEFILES


def test_build_refuses_when_a_required_artifact_is_missing(
    fake_repo: Path, tmp_path: Path
):
    (fake_repo / "infra/cfn/queue/queue.yml").unlink()
    _git(fake_repo, "add", "-A")
    _git(fake_repo, "commit", "-q", "-m", "drop queue template")

    with pytest.raises(AssertionError, match="missing artifacts"):
        workspace.build(tmp_path / "out", repo=fake_repo)


def test_building_leaves_the_repository_status_unchanged(fake_repo: Path, tmp_path: Path):
    before = subprocess.run(  # nosec B603 B607
        ["git", "status", "--porcelain"],
        cwd=fake_repo, capture_output=True, text=True, check=True,
    ).stdout
    workspace.build(tmp_path / "out", repo=fake_repo)
    after = subprocess.run(  # nosec B603 B607
        ["git", "status", "--porcelain"],
        cwd=fake_repo, capture_output=True, text=True, check=True,
    ).stdout
    assert before == after


def test_the_real_repository_builds_clean(tmp_path: Path):
    """The assertions run against THIS repository, not only a fixture."""
    src = workspace.build(tmp_path / "out", repo=workspace.REPO_ROOT)
    assert src.file_count > 100
    assert not (src.root / ".env").exists()
    for name in workspace.GATING_MAKEFILES:
        assert not (src.root / "scripts" / name).exists(), name
    # The skills under test, the tier templates and both application trees.
    assert (src.root / ".claude/skills/ipa-compose/SKILL.md").is_file()
    assert (src.root / "infra/cfn/frontend/frontend.yml").is_file()
    assert (src.root / "web-client/package.json").is_file()
    assert (src.root / "app-lib/pyproject.toml").is_file()
