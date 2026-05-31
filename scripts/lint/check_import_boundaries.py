#!/usr/bin/env python3
"""Check that features do not import from other features.

Enforces the Orchestration-Only Composition pattern: features import from
common/ and their own subdirectories only. Cross-feature wiring belongs in
the composition roots (common/app.py, common/lambda/*.py).

Usage:
    python check_import_boundaries.py <src_root>
    python check_import_boundaries.py src/app_lib
"""

import ast
import sys
from pathlib import Path
from typing import Optional


def get_feature_name(file_path: Path, features_dir: Path) -> Optional[str]:
    """Extract feature name from path (first directory under features/)."""
    try:
        rel = file_path.relative_to(features_dir)
        return rel.parts[0] if rel.parts else None
    except ValueError:
        return None


def check_import(node: ast.AST, feature_name: str) -> Optional[str]:
    """Return offending module path if this import crosses a feature boundary."""
    if isinstance(node, ast.ImportFrom) and node.module:
        parts = node.module.split(".")
        if len(parts) >= 3 and parts[0] == "app_lib" and parts[1] == "features":
            if parts[2] != feature_name:
                return node.module
    elif isinstance(node, ast.Import):
        for alias in node.names:
            parts = alias.name.split(".")
            if len(parts) >= 3 and parts[0] == "app_lib" and parts[1] == "features":
                if parts[2] != feature_name:
                    return alias.name
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <src_root>", file=sys.stderr)
        return 2

    src_root = Path(sys.argv[1])
    features_dir = src_root / "features"

    if not features_dir.is_dir():
        print(f"ERROR: {features_dir} is not a directory", file=sys.stderr)
        return 2

    violations = []
    files_checked = 0

    for py_file in sorted(features_dir.rglob("*.py")):
        feature_name = get_feature_name(py_file, features_dir)
        if not feature_name:
            continue

        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
            continue

        files_checked += 1
        for node in ast.walk(tree):
            offending = check_import(node, feature_name)
            if offending:
                violations.append((py_file, node.lineno, offending, feature_name))

    if violations:
        print("\n\033[1;31mOrchestration-Only Composition violations:\033[0m\n")
        for path, line, module, feature in violations:
            print(f"  {path}:{line}")
            print(f"    imports {module} (from inside features/{feature}/)")
            print()
        print(
            "  This is a cross-feature import. Features must not import from "
            "other features."
        )
        print(
            "  See: app-lib/src/app_lib/features/CLAUDE.md → "
            "'When You Think You Need a Cross-Feature Import'"
        )
        print(
            f"\n\033[1;31mFound {len(violations)} violation(s) "
            f"in {files_checked} files.\033[0m"
        )
        return 1

    print(
        f"\033[0;32m✓ Import boundaries clean: "
        f"checked {files_checked} files, 0 violations.\033[0m"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
