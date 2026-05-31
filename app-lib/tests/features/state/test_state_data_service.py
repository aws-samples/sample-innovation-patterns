# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for StateDataService.

Verifies CRUD operations and singleton state management against mocked
PynamoDB StateTable.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app_lib.features.state.model.state_table import StateTable
from app_lib.features.state.service.state_data_service import (
    SINGLETON_ID,
    VALID_LEVELS,
    StateDataService,
)


@pytest.fixture
def service():
    """Create data service instance."""
    return StateDataService()


@pytest.fixture
def mock_state():
    """Create mock state record."""
    state = MagicMock(spec=StateTable)
    state.id = SINGLETON_ID
    state.level = "mid"
    state.updated_at = datetime.now(timezone.utc).isoformat()
    return state


@patch.object(StateTable, "get")
def test_get_success(mock_get, service, mock_state):
    """Test getting state by ID."""
    mock_get.return_value = mock_state
    result = service.get(SINGLETON_ID)
    assert result == mock_state
    mock_get.assert_called_once_with(SINGLETON_ID)


@patch.object(StateTable, "get")
def test_get_not_found(mock_get, service):
    """Test getting non-existent state."""
    mock_get.side_effect = StateTable.DoesNotExist
    result = service.get("nonexistent")
    assert result is None


@patch.object(StateTable, "save")
def test_save(mock_save, service, mock_state):
    """Test saving state."""
    service.save(mock_state)
    mock_state.save.assert_called_once()


@patch.object(StateTable, "get")
def test_delete_existing(mock_get, service, mock_state):
    """Test deleting an existing state returns True."""
    mock_get.return_value = mock_state
    result = service.delete(SINGLETON_ID)
    assert result is True
    mock_state.delete.assert_called_once()


@patch.object(StateTable, "get")
def test_delete_not_found(mock_get, service):
    """Test deleting a non-existent state returns False."""
    mock_get.side_effect = StateTable.DoesNotExist
    result = service.delete("nonexistent")
    assert result is False


@patch.object(StateTable, "scan")
def test_list(mock_scan, service, mock_state):
    """Test listing state records."""
    mock_scan.return_value = [mock_state]
    result = service.list(limit=10)
    assert len(result) == 1
    assert result[0] == mock_state
    mock_scan.assert_called_once_with(limit=10)


@patch.object(StateTable, "scan")
def test_query_with_filters(mock_scan, service, mock_state):
    """Test querying state records with filters."""
    mock_scan.return_value = [mock_state]
    result = service.query(level="mid", limit=10)
    assert len(result) == 1
    assert result[0].level == "mid"


@patch.object(StateTable, "scan")
def test_query_no_filters(mock_scan, service, mock_state):
    """Test querying without filters returns all."""
    mock_scan.return_value = [mock_state]
    result = service.query(limit=10)
    assert len(result) == 1


@patch.object(StateTable, "count")
def test_count(mock_count, service):
    """Test counting state records."""
    mock_count.return_value = 1
    result = service.count()
    assert result == 1
    mock_count.assert_called_once()


@patch.object(StateTable, "get")
def test_get_current(mock_get, service, mock_state):
    """Test getting the current singleton state."""
    mock_get.return_value = mock_state
    result = service.get_current()
    assert result == mock_state
    mock_get.assert_called_once_with(SINGLETON_ID)


@patch.object(StateDataService, "save")
def test_randomize_creates_state_with_valid_level(mock_save, service):
    """Test randomize creates state with valid level."""
    result = service.randomize()
    assert result.id == SINGLETON_ID
    assert result.level in VALID_LEVELS
    assert result.updated_at is not None
    mock_save.assert_called_once()


@patch.object(StateDataService, "save")
def test_randomize_generates_different_levels(mock_save, service):
    """Test randomize can generate all valid levels."""
    levels_seen = set()
    # Run multiple times to increase chance of seeing all levels
    for _ in range(50):
        result = service.randomize()
        levels_seen.add(result.level)
    # Should see at least 2 different levels in 50 tries
    assert len(levels_seen) >= 2
    # All levels should be valid
    assert all(level in VALID_LEVELS for level in levels_seen)


@patch.object(StateDataService, "get_current")
@patch.object(StateDataService, "randomize")
def test_initialize_if_missing_creates_when_absent(
    mock_randomize, mock_get_current, service, mock_state
):
    """Test initialize_if_missing creates state when absent."""
    mock_get_current.return_value = None
    mock_randomize.return_value = mock_state
    result = service.initialize_if_missing()
    assert result == mock_state
    mock_get_current.assert_called_once()
    mock_randomize.assert_called_once()


@patch.object(StateDataService, "get_current")
@patch.object(StateDataService, "randomize")
def test_initialize_if_missing_returns_existing(
    mock_randomize, mock_get_current, service, mock_state
):
    """Test initialize_if_missing returns existing state."""
    mock_get_current.return_value = mock_state
    result = service.initialize_if_missing()
    assert result == mock_state
    mock_get_current.assert_called_once()
    mock_randomize.assert_not_called()
