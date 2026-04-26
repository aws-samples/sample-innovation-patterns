# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# Copyright © Amazon.com and Affiliates:
# This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties.
# The libraries used in this developed content are subject to their respective license disclosures.
# Please see the license and SBOM artifact files included in this repository for specific license references.

"""Path utility for resolving project paths."""

import os
import pathlib
from typing import Optional


class PathUtil:
    """Utility class for resolving paths relative to the library and repository root."""

    @staticmethod
    def lib_root(path: Optional[str] = None) -> str:
        """Get path to library root (src/app_lib) or file within it.

        Args:
            path: Optional relative path within library root

        Returns:
            Absolute path to library root or specified file

        Example:
            >>> PathUtil.lib_root()  # Returns path to src/app_lib/
            >>> PathUtil.lib_root("model")  # Returns path to src/app_lib/model/
        """
        current_file = pathlib.Path(__file__)
        project_root = (
            current_file.parent.parent.parent
        )  # common/util/ → common/ → app_lib/

        if path:
            if os.path.isabs(path):
                path = os.path.relpath(path, "/")
            project_root = os.path.join(project_root, path)

        return str(project_root)

    @staticmethod
    def project_root(path: Optional[str] = None) -> str:
        """Get path to repository root or file within it.

        Args:
            path: Optional relative path within repository root

        Returns:
            Absolute path to repository root or specified file

        Example:
            >>> PathUtil.project_root()  # Returns path to app-lib/
            >>> PathUtil.project_root("tests")  # Returns path to app-lib/tests/
        """
        root_path = PathUtil.lib_root("../../")

        if path:
            if os.path.isabs(path):
                path = os.path.relpath(path, "/")
            root_path = os.path.join(root_path, path)

        return root_path

    @staticmethod
    def lib_assets(path: Optional[str] = None) -> str:
        """Get path to assets directory or file within assets.

        Args:
            path: Optional relative path within assets directory

        Returns:
            Absolute path to assets directory or specified file

        Example:
            >>> PathUtil.lib_assets()  # Returns path to assets/
            >>> PathUtil.lib_assets("datasets/titanic.csv")  # Returns path to assets/datasets/titanic.csv
        """
        return PathUtil.lib_root(f"assets/{path}" if path else "assets")

    @staticmethod
    def resolve_path(path: str) -> str:
        """Determine if a path is relative or absolute and return the appropriate resolved path.

        Args:
            path: The input path string to resolve

        Returns:
            If absolute path, returns the absolute path as-is.
            If relative path, returns the path relative to the library root.

        Example:
            >>> PathUtil.resolve_path('/absolute/path/to/file')
            '/absolute/path/to/file'
            >>> PathUtil.resolve_path('relative/path/to/file')
            '/path/to/lib/root/relative/path/to/file'
        """
        if os.path.isabs(path):
            return path
        else:
            return PathUtil.lib_root(path)
