# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for StateTable PynamoDB model.

Verifies table name generation and attribute definitions.
"""

from app_lib.features.state.model.state_table import StateTable


def test_table_name():
    """Test that table name includes environment prefix."""
    assert StateTable.Meta.table_name.endswith("_state")


def test_has_required_attributes():
    """Test that model has required attributes."""
    assert hasattr(StateTable, "id")
    assert hasattr(StateTable, "level")
    assert hasattr(StateTable, "updated_at")


def test_id_is_hash_key():
    """Test that id is the hash key."""
    assert StateTable.id.is_hash_key
