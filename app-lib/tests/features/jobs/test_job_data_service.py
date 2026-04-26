# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for JobDataService.

Verifies CRUD operations against mocked PynamoDB JobTable.
"""

from unittest.mock import MagicMock, patch

import pytest

from app_lib.features.jobs.model.job_table import JobTable
from app_lib.features.jobs.service.job_data_service import JobDataService


@pytest.fixture
def service():
    """Create data service instance."""
    return JobDataService()


@pytest.fixture
def mock_job():
    """Create mock job."""
    job = MagicMock(spec=JobTable)
    job.id = "abc-123"
    job.status = "PENDING"
    job.job_type = "passenger_analysis"
    job.input_data = '{"ticket": "113803"}'
    job.metadata = None
    job.error = None
    job.created_at = "2026-04-09T20:00:00+00:00"
    job.updated_at = "2026-04-09T20:00:00+00:00"
    return job


@patch.object(JobTable, "get")
def test_get_success(mock_get, service, mock_job):
    """Test getting job by ID."""
    mock_get.return_value = mock_job
    result = service.get("abc-123")
    assert result == mock_job
    mock_get.assert_called_once_with("abc-123")


@patch.object(JobTable, "get")
def test_get_not_found(mock_get, service):
    """Test getting non-existent job."""
    mock_get.side_effect = JobTable.DoesNotExist
    result = service.get("INVALID")
    assert result is None


@patch.object(JobTable, "save")
def test_save(mock_save, service, mock_job):
    """Test saving job."""
    service.save(mock_job)
    mock_job.save.assert_called_once()


@patch.object(JobTable, "get")
def test_delete_existing(mock_get, service, mock_job):
    """Test deleting an existing job returns True."""
    mock_get.return_value = mock_job
    result = service.delete("abc-123")
    assert result is True
    mock_job.delete.assert_called_once()


@patch.object(JobTable, "get")
def test_delete_not_found(mock_get, service):
    """Test deleting a non-existent job returns False."""
    mock_get.side_effect = JobTable.DoesNotExist
    result = service.delete("INVALID")
    assert result is False


@patch.object(JobTable, "scan")
def test_list(mock_scan, service, mock_job):
    """Test listing jobs."""
    mock_scan.return_value = [mock_job]
    result = service.list(limit=10)
    assert len(result) == 1
    assert result[0] == mock_job
    mock_scan.assert_called_once_with(limit=10)


@patch.object(JobTable, "scan")
def test_query_by_status(mock_scan, service, mock_job):
    """Test querying jobs by status."""
    mock_scan.return_value = [mock_job]
    result = service.query(status="PENDING", limit=10)
    assert len(result) == 1
    assert result[0].status == "PENDING"


@patch.object(JobTable, "scan")
def test_query_by_job_type(mock_scan, service, mock_job):
    """Test querying jobs by job type."""
    mock_scan.return_value = [mock_job]
    result = service.query(job_type="passenger_analysis", limit=10)
    assert len(result) == 1
    assert result[0].job_type == "passenger_analysis"


@patch.object(JobTable, "scan")
def test_query_no_filters(mock_scan, service, mock_job):
    """Test querying without filters returns all."""
    mock_scan.return_value = [mock_job]
    result = service.query(limit=10)
    assert len(result) == 1


@patch.object(JobTable, "count")
def test_count(mock_count, service):
    """Test counting jobs."""
    mock_count.return_value = 42
    result = service.count()
    assert result == 42
    mock_count.assert_called_once()
