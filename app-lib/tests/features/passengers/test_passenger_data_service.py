# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for TitanicPassengerDataService.

Verifies CRUD operations against mocked PynamoDB TitanicPassengerTable.
"""

from unittest.mock import MagicMock, patch

import pytest

from app_lib.features.passengers.model.passenger_table import TitanicPassengerTable
from app_lib.features.passengers.service.passenger_data_service import (
    TitanicPassengerDataService,
)


@pytest.fixture
def repository():
    """Create data service instance."""
    return TitanicPassengerDataService()


@pytest.fixture
def mock_passenger():
    """Create mock passenger."""
    passenger = MagicMock(spec=TitanicPassengerTable)
    passenger.id = "24160"
    passenger.name = "Allen, Miss. Elisabeth Walton"
    passenger.pclass = 1
    passenger.survived = 1
    return passenger


@patch.object(TitanicPassengerTable, "get")
def test_get_success(mock_get, repository, mock_passenger):
    """Test getting passenger by ticket."""
    mock_get.return_value = mock_passenger
    result = repository.get("24160")
    assert result == mock_passenger
    mock_get.assert_called_once_with("24160")


@patch.object(TitanicPassengerTable, "get")
def test_get_not_found(mock_get, repository):
    """Test getting non-existent passenger."""
    mock_get.side_effect = TitanicPassengerTable.DoesNotExist
    result = repository.get("INVALID")
    assert result is None


@patch.object(TitanicPassengerTable, "save")
def test_save(mock_save, repository, mock_passenger):
    """Test saving passenger."""
    repository.save(mock_passenger)
    mock_passenger.save.assert_called_once()


@patch.object(TitanicPassengerTable, "get")
def test_delete_existing(mock_get, repository, mock_passenger):
    """Test deleting an existing passenger returns True."""
    mock_get.return_value = mock_passenger
    result = repository.delete("24160")
    assert result is True
    mock_passenger.delete.assert_called_once()


@patch.object(TitanicPassengerTable, "get")
def test_delete_not_found(mock_get, repository):
    """Test deleting a non-existent passenger returns False."""
    mock_get.side_effect = TitanicPassengerTable.DoesNotExist
    result = repository.delete("INVALID")
    assert result is False


@patch.object(TitanicPassengerTable, "scan")
def test_list(mock_scan, repository, mock_passenger):
    """Test listing passengers."""
    mock_scan.return_value = [mock_passenger]
    result = repository.list(limit=10)
    assert len(result) == 1
    assert result[0] == mock_passenger
    mock_scan.assert_called_once_with(limit=10)


@patch.object(TitanicPassengerTable, "scan")
def test_query_by_class(mock_scan, repository, mock_passenger):
    """Test querying passengers by class."""
    mock_scan.return_value = [mock_passenger]
    result = repository.query(pclass=1, limit=10)
    assert len(result) == 1
    assert result[0].pclass == 1


@patch.object(TitanicPassengerTable, "scan")
def test_query_survivors(mock_scan, repository, mock_passenger):
    """Test querying survivors."""
    mock_scan.return_value = [mock_passenger]
    result = repository.query(survived=1, limit=10)
    assert len(result) == 1
    assert result[0].survived == 1


@patch.object(TitanicPassengerTable, "scan")
def test_query_by_sex(mock_scan, repository, mock_passenger):
    """Test querying passengers by sex."""
    mock_passenger.sex = "female"
    mock_scan.return_value = [mock_passenger]
    result = repository.query(sex="female", limit=10)
    assert len(result) == 1
    assert result[0].sex == "female"


@patch.object(TitanicPassengerTable, "scan")
def test_query_multiple_filters(mock_scan, repository, mock_passenger):
    """Test querying with multiple filters."""
    mock_passenger.sex = "female"
    mock_scan.return_value = [mock_passenger]
    result = repository.query(pclass=1, sex="female", survived=1, limit=10)
    assert len(result) == 1
    assert result[0].pclass == 1
    assert result[0].sex == "female"
    assert result[0].survived == 1


@patch.object(TitanicPassengerTable, "scan")
def test_query_no_filters(mock_scan, repository, mock_passenger):
    """Test querying without filters returns all."""
    mock_scan.return_value = [mock_passenger]
    result = repository.query(limit=10)
    assert len(result) == 1


@patch.object(TitanicPassengerTable, "count")
def test_count(mock_count, repository):
    """Test counting passengers."""
    mock_count.return_value = 42
    result = repository.count()
    assert result == 42
    mock_count.assert_called_once()
