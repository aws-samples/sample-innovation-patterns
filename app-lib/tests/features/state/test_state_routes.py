# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for state REST API routes.

Verifies GET /api/v1/state and POST /api/v1/state/randomize endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app_lib.features.state.model.state_table import StateTable
from app_lib.features.state.service.state_data_service import SINGLETON_ID


@pytest.fixture
def client():
    """Create test client with auth disabled."""
    with patch.dict("os.environ", {"AUTH_ENABLED": "false"}):
        from app_lib.common.app import app

        return TestClient(app)


@pytest.fixture
def mock_state():
    """Create mock state record."""
    state = MagicMock(spec=StateTable)
    state.id = SINGLETON_ID
    state.level = "mid"
    state.updated_at = datetime.now(timezone.utc).isoformat()
    return state


@patch("app_lib.features.state.routes.state_routes.state_service.initialize_if_missing")
def test_get_current_state_success(mock_initialize, mock_state, client):
    """Test GET /api/v1/state returns current state."""
    mock_initialize.return_value = mock_state

    response = client.get("/api/v1/state")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == SINGLETON_ID
    assert data["level"] == "mid"
    assert "updated_at" in data
    mock_initialize.assert_called_once()


@patch("app_lib.features.state.routes.state_routes.state_service.initialize_if_missing")
def test_get_current_state_table_not_available(mock_initialize, client):
    """Test GET /api/v1/state handles missing table."""
    mock_initialize.side_effect = Exception("ResourceNotFoundException")

    response = client.get("/api/v1/state")

    assert response.status_code == 503
    assert "State table not available" in response.json()["detail"]


@patch("app_lib.features.state.routes.state_routes.state_service.randomize")
def test_randomize_state_success(mock_randomize, mock_state, client):
    """Test POST /api/v1/state/randomize creates new random state."""
    mock_state.level = "high"
    mock_randomize.return_value = mock_state

    response = client.post("/api/v1/state/randomize")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == SINGLETON_ID
    assert data["level"] == "high"
    assert "updated_at" in data
    mock_randomize.assert_called_once()


@patch("app_lib.features.state.routes.state_routes.state_service.randomize")
def test_randomize_state_table_not_available(mock_randomize, client):
    """Test POST /api/v1/state/randomize handles missing table."""
    mock_randomize.side_effect = Exception("ResourceNotFoundException")

    response = client.post("/api/v1/state/randomize")

    assert response.status_code == 503
    assert "State table not available" in response.json()["detail"]


@patch("app_lib.features.state.routes.state_routes.state_service.randomize")
def test_randomize_updates_timestamp(mock_randomize, mock_state, client):
    """Test randomize updates the timestamp."""
    old_time = "2024-01-01T00:00:00+00:00"
    new_time = datetime.now(timezone.utc).isoformat()
    mock_state.updated_at = new_time
    mock_randomize.return_value = mock_state

    response = client.post("/api/v1/state/randomize")

    assert response.status_code == 200
    data = response.json()
    assert data["updated_at"] == new_time
    assert data["updated_at"] != old_time
