#!/usr/bin/env python3
"""Centralized version script for build and deploy workflows.

Reads the canonical version from app-lib/pyproject.toml and combines it
with the current git SHA to produce version strings for Docker tags,
semver metadata, and build identification.

Usage:
    python scripts/util/version.py docker   # 0.1.0-abc1234
    python scripts/util/version.py semver   # 0.1.0+abc1234
    python scripts/util/version.py version  # 0.1.0
    python scripts/util/version.py sha      # abc1234

SHA resolution (first match wins):
    1. CODEBUILD_RESOLVED_SOURCE_VERSION env var (AWS CodeBuild)
    2. git rev-parse --short=7 HEAD (local dev)
    3. "unknown" (fallback)

Requires Python 3.12+ (stdlib tomllib). No external dependencies.
"""

import os
import subprocess
import sys
import tomllib
from pathlib import Path

PYPROJECT_PATH = Path(__file__).resolve().parents[2] / "app-lib" / "pyproject.toml"


def get_version() -> str:
    """Read version from app-lib/pyproject.toml."""
    try:
        with open(PYPROJECT_PATH, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except FileNotFoundError:
        print(f"error: {PYPROJECT_PATH} not found", file=sys.stderr)
        sys.exit(1)
    except KeyError:
        print(f"error: no project.version in {PYPROJECT_PATH}", file=sys.stderr)
        sys.exit(1)


def get_sha() -> str:
    """Resolve short git SHA from env var or git CLI."""
    # AWS CodeBuild provides the full commit SHA
    cb_sha = os.environ.get("CODEBUILD_RESOLVED_SOURCE_VERSION")
    if cb_sha:
        return cb_sha[:7]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> None:
    commands = {
        "docker": lambda v, s: f"{v}-{s}",
        "semver": lambda v, s: f"{v}+{s}",
        "version": lambda v, s: v,
        "sha": lambda v, s: s,
    }

    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print(f"usage: {sys.argv[0]} {{{','.join(commands)}}}", file=sys.stderr)
        sys.exit(1)

    version = get_version()
    sha = get_sha()
    print(commands[sys.argv[1]](version, sha))


if __name__ == "__main__":
    main()
