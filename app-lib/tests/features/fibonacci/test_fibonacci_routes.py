# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for Fibonacci REST API routes."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app_lib.features.fibonacci.model.fibonacci_table import FibonacciTable


@pytest.fixture
def client():
    """Create test client with auth disabled."""
    with patch.dict("os.environ", {"AUTH_ENABLED": "false"}):
        from app_lib.common.app import app

        return TestClient(app)


@pytest.fixture
def mock_fibonacci_record():
    """Create a mock Fibonacci record."""
    record = MagicMock(spec=FibonacciTable)
    record.id = "test-uuid-123"
    record.value = 8
    record.created_at = "2026-05-31T10:00:00+00:00"
    return record


def test_create_fibonacci(client, mock_fibonacci_record):
    """Test creating a new Fibonacci record."""
    with (
        patch("uuid.uuid4", return_value="test-uuid-123"),
        patch(
            "app_lib.features.fibonacci.routes.fibonacci_routes._random_fibonacci_value",
            return_value=8,
        ),
        patch(
            "app_lib.features.fibonacci.routes.fibonacci_routes.data_service.save"
        ) as mock_save,
    ):
        response = client.post("/api/v1/fibonacci")

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-uuid-123"
        assert data["value"] == 8
        assert "created_at" in data
        mock_save.assert_called_once()


def test_list_fibonacci_empty(client):
    """Test listing Fibonacci records when none exist."""
    with patch(
        "app_lib.features.fibonacci.routes.fibonacci_routes.data_service.list",
        return_value=[],
    ):
        response = client.get("/api/v1/fibonacci")
        assert response.status_code == 200
        data = response.json()
        assert data == []


def test_list_fibonacci_with_records(client):
    """Test listing Fibonacci records."""
    mock_records = [
        MagicMock(id="id1", value=1, created_at="2026-05-31T12:00:00+00:00"),  # newer
        MagicMock(id="id2", value=2, created_at="2026-05-31T10:00:00+00:00"),  # older
    ]
    with patch(
        "app_lib.features.fibonacci.routes.fibonacci_routes.data_service.list",
        return_value=mock_records,
    ):
        response = client.get("/api/v1/fibonacci")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Verify newest first
        assert data[0]["id"] == "id1"
        assert data[1]["id"] == "id2"


def test_get_fibonacci_existing(client, mock_fibonacci_record):
    """Test retrieving an existing Fibonacci record."""
    with patch(
        "app_lib.features.fibonacci.routes.fibonacci_routes.data_service.get",
        return_value=mock_fibonacci_record,
    ):
        response = client.get("/api/v1/fibonacci/test-uuid-123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-uuid-123"
        assert data["value"] == 8


def test_get_fibonacci_not_found(client):
    """Test retrieving a nonexistent Fibonacci record."""
    with patch(
        "app_lib.features.fibonacci.routes.fibonacci_routes.data_service.get",
        return_value=None,
    ):
        response = client.get("/api/v1/fibonacci/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_delete_fibonacci_existing(client):
    """Test deleting an existing Fibonacci record."""
    with patch(
        "app_lib.features.fibonacci.routes.fibonacci_routes.data_service.delete",
        return_value=True,
    ):
        response = client.delete("/api/v1/fibonacci/test-uuid-123")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True


def test_delete_fibonacci_not_found(client):
    """Test deleting a nonexistent Fibonacci record."""
    with patch(
        "app_lib.features.fibonacci.routes.fibonacci_routes.data_service.delete",
        return_value=False,
    ):
        response = client.delete("/api/v1/fibonacci/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_fibonacci_sequence_generation():
    """Test the Fibonacci sequence generation function."""
    from app_lib.features.fibonacci.routes.fibonacci_routes import (
        _generate_fibonacci_sequence,
    )

    # Test F(1) through F(15)
    fib_15 = _generate_fibonacci_sequence(15)
    assert len(fib_15) == 15
    assert fib_15[0] == 1  # F(1)
    assert fib_15[1] == 1  # F(2)
    assert fib_15[2] == 2  # F(3)
    assert fib_15[3] == 3  # F(4)
    assert fib_15[4] == 5  # F(5)
    assert fib_15[5] == 8  # F(6)
    assert fib_15[14] == 610  # F(15)


def test_random_fibonacci_value_in_range():
    """Test that random Fibonacci value is valid."""
    from app_lib.features.fibonacci.routes.fibonacci_routes import (
        _random_fibonacci_value,
    )

    valid_values = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]

    # Generate multiple values to test randomness
    for _ in range(10):
        value = _random_fibonacci_value()
        assert value in valid_values
