# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#!/usr/bin/env python3
"""Centralized version script for build and deploy workflows.

Reads the canonical version from app-lib/pyproject.toml and combines it
with the current git SHA to produce version strings for Docker tags,
semver metadata, and build identification.

Usage:
    python infra/scripts/version.py docker   # 0.1.0-abc1234
    python infra/scripts/version.py semver   # 0.1.0+abc1234
    python infra/scripts/version.py version  # 0.1.0
    python infra/scripts/version.py sha      # abc1234

SHA resolution (first match wins):
    1. CODEBUILD_RESOLVED_SOURCE_VERSION env var (AWS CodeBuild)
    2. git rev-parse --short=7 HEAD (local dev)
    3. "unknown" (fallback)

Requires Python 3.12+ (stdlib tomllib). No external dependencies.
"""

import os
import subprocess
import sys
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        import re as _re, sys as _sys2
        # Minimal fallback: parse version from pyproject.toml without tomllib
        def _fallback_load(f):
            text = f.read().decode()
            m = _re.search(r'^version\s*=\s*"([^"]+)"', text, _re.MULTILINE)
            if m:
                return {"project": {"version": m.group(1)}}
            raise KeyError("project.version")
        tomllib = type(_sys2)("_fallback_tomllib")  # type: ignore[assignment]
        tomllib.load = _fallback_load  # type: ignore[attr-defined]
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
