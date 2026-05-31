# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for FibonacciDataService."""

from unittest.mock import MagicMock, patch

import pytest

from app_lib.features.fibonacci.model.fibonacci_table import FibonacciTable
from app_lib.features.fibonacci.service.fibonacci_data_service import (
    FibonacciDataService,
)


@pytest.fixture
def service():
    """Create a FibonacciDataService instance."""
    return FibonacciDataService()


@pytest.fixture
def sample_record():
    """Create a sample FibonacciTable record."""
    record = MagicMock(spec=FibonacciTable)
    record.id = "test-id-123"
    record.value = 5
    record.created_at = "2026-05-31T10:00:00+00:00"
    return record


def test_get_existing_record(service, sample_record):
    """Test retrieving an existing Fibonacci record."""
    with patch.object(FibonacciTable, "get", return_value=sample_record):
        result = service.get("test-id-123")
        assert result is not None
        assert result.id == "test-id-123"
        assert result.value == 5


def test_get_nonexistent_record(service):
    """Test retrieving a nonexistent record returns None."""
    with patch.object(FibonacciTable, "get", side_effect=FibonacciTable.DoesNotExist):
        result = service.get("nonexistent-id")
        assert result is None


def test_save_record(service, sample_record):
    """Test saving a Fibonacci record."""
    sample_record.save = MagicMock()
    service.save(sample_record)
    sample_record.save.assert_called_once()


def test_delete_existing_record(service, sample_record):
    """Test deleting an existing record."""
    sample_record.delete = MagicMock()
    with patch.object(FibonacciTable, "get", return_value=sample_record):
        result = service.delete("test-id-123")
        assert result is True
        sample_record.delete.assert_called_once()


def test_delete_nonexistent_record(service):
    """Test deleting a nonexistent record returns False."""
    with patch.object(FibonacciTable, "get", side_effect=FibonacciTable.DoesNotExist):
        result = service.delete("nonexistent-id")
        assert result is False


def test_list_records(service):
    """Test listing Fibonacci records."""
    mock_records = [
        MagicMock(id="id1", value=1, created_at="2026-05-31T10:00:00+00:00"),
        MagicMock(id="id2", value=2, created_at="2026-05-31T11:00:00+00:00"),
        MagicMock(id="id3", value=3, created_at="2026-05-31T12:00:00+00:00"),
    ]
    with patch.object(FibonacciTable, "scan", return_value=iter(mock_records)):
        results = service.list(limit=100)
        assert len(results) == 3
        assert results[0].id == "id1"


def test_query_with_filters(service):
    """Test querying records with filters."""
    mock_records = [
        MagicMock(id="id1", value=5, created_at="2026-05-31T10:00:00+00:00"),
        MagicMock(id="id2", value=8, created_at="2026-05-31T11:00:00+00:00"),
        MagicMock(id="id3", value=5, created_at="2026-05-31T12:00:00+00:00"),
    ]
    with patch.object(FibonacciTable, "scan", return_value=iter(mock_records)):
        results = service.query(limit=100, value=5)
        assert len(results) == 2
        assert all(r.value == 5 for r in results)


def test_query_without_filters(service):
    """Test querying records without filters returns all."""
    mock_records = [
        MagicMock(id="id1", value=1, created_at="2026-05-31T10:00:00+00:00"),
        MagicMock(id="id2", value=2, created_at="2026-05-31T11:00:00+00:00"),
    ]
    with patch.object(FibonacciTable, "scan", return_value=iter(mock_records)):
        results = service.query(limit=100)
        assert len(results) == 2


def test_count(service):
    """Test counting records."""
    with patch.object(FibonacciTable, "count", return_value=42):
        result = service.count()
        assert result == 42
