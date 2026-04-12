# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Basic smoke test."""


def test_import():
    """Test that the package can be imported."""
    import app_lib

    assert app_lib is not None
