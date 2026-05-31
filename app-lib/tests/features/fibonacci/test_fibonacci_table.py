# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for FibonacciTable model."""

import pytest

from app_lib.features.fibonacci.model.fibonacci_table import FibonacciTable


@pytest.fixture
def fibonacci_data():
    """Sample Fibonacci record data."""
    return {
        "id": "abc-123-def",
        "value": 8,
        "created_at": "2026-05-31T10:00:00+00:00",
    }


def test_fibonacci_model_attributes(fibonacci_data):
    """Test Fibonacci model has correct attributes."""
    record = FibonacciTable(**fibonacci_data)
    assert record.id == "abc-123-def"
    assert record.value == 8
    assert record.created_at == "2026-05-31T10:00:00+00:00"


def test_fibonacci_model_all_fields_required():
    """Test Fibonacci model requires all fields."""
    record = FibonacciTable(
        id="test-uuid",
        value=13,
        created_at="2026-05-31T12:00:00+00:00",
    )
    assert record.id == "test-uuid"
    assert record.value == 13
    assert record.created_at == "2026-05-31T12:00:00+00:00"


def test_fibonacci_table_name():
    """Test table name uses PynamodbUtil prefix."""
    assert "fibonacci" in FibonacciTable.Meta.table_name
