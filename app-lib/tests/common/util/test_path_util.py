# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for PathUtil."""

import os

from app_lib.common.util.path_util import PathUtil


def test_lib_root_returns_path():
    """Test lib_root returns a valid path."""
    result = os.path.normpath(PathUtil.lib_root())
    assert result is not None
    assert os.path.exists(result)
    assert result.endswith("app_lib")


def test_lib_root_with_subpath():
    """Test lib_root with relative path."""
    result = os.path.normpath(PathUtil.lib_root("common"))
    assert result.endswith(os.path.join("app_lib", "common"))
    assert os.path.exists(result)


def test_lib_assets_returns_path():
    """Test lib_assets returns valid path."""
    result = os.path.normpath(PathUtil.lib_assets())
    assert result is not None
    assert result.endswith(os.path.join("app_lib", "assets"))


def test_lib_assets_with_subpath():
    """Test lib_assets with relative path."""
    result = os.path.normpath(PathUtil.lib_assets("datasets"))
    assert result.endswith(os.path.join("app_lib", "assets", "datasets"))


def test_path_hierarchy():
    """Test that paths maintain correct hierarchy."""
    lib = os.path.normpath(PathUtil.lib_root())
    assets = os.path.normpath(PathUtil.lib_assets())
    repo = os.path.normpath(PathUtil.project_root())

    # Assets should be under lib_root
    assert assets.startswith(lib)

    # lib_root should be under repo_root
    assert lib in repo or os.path.commonpath([lib, repo]) == repo


def test_lib_assets_file_path():
    """Test lib_assets with file path."""
    result = PathUtil.lib_assets("datasets/titanic/walkthrough_titanic.csv")
    assert (
        "assets" in result
        and "datasets" in result
        and "walkthrough_titanic.csv" in result
    )
    assert os.path.exists(result)
