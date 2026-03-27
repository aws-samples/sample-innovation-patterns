#!/usr/bin/env python3
"""Build version management utilities.

Reads and increments the build version number stored in BUILD.txt.
"""

import sys
from pathlib import Path

BUILD_FILE = Path(__file__).parent.parent / "BUILD.txt"


def read():
    """Read the current build version number from BUILD.txt."""
    if not BUILD_FILE.exists():
        BUILD_FILE.write_text("0\n")
        return 0
    return int(BUILD_FILE.read_text().strip())


def increment():
    """Increment and return the new build version number."""
    version = read() + 1
    BUILD_FILE.write_text(f"{version}\n")
    return version


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "read"
    if cmd == "increment":
        print(increment())
    else:
        print(read())
