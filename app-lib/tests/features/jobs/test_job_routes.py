# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for job route handlers with mocked services."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app_lib.features.jobs.model.job_table import JobTable


@pytest.fixture
def mock_job():
    """Create a mock job model."""
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


@pytest.fixture
def client():
    """Create test client with auth disabled."""
    with patch.dict("os.environ", {"AUTH_ENABLED": "false"}):
        from app_lib.common.app import app

        return TestClient(app)


@patch("app_lib.features.jobs.routes.job_routes.job_service")
def test_get_job(mock_service, client, mock_job):
    """Test GET /api/v1/jobs/{job_id} returns job."""
    mock_service.get.return_value = mock_job
    resp = client.get("/api/v1/jobs/abc-123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "abc-123"
    assert data["status"] == "PENDING"


@patch("app_lib.features.jobs.routes.job_routes.job_service")
def test_get_job_not_found(mock_service, client):
    """Test GET /api/v1/jobs/{job_id} returns 404 when not found."""
    mock_service.get.return_value = None
    resp = client.get("/api/v1/jobs/not-exist")
    assert resp.status_code == 404


@patch("app_lib.features.jobs.routes.job_routes.job_service")
def test_list_jobs(mock_service, client, mock_job):
    """Test GET /api/v1/jobs returns list of jobs."""
    mock_service.query.return_value = [mock_job]
    resp = client.get("/api/v1/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["job_id"] == "abc-123"


@patch("app_lib.features.jobs.routes.job_routes.job_service")
def test_list_jobs_with_status_filter(mock_service, client, mock_job):
    """Test GET /api/v1/jobs?status=PENDING filters correctly."""
    mock_service.query.return_value = [mock_job]
    resp = client.get("/api/v1/jobs?status=PENDING")
    assert resp.status_code == 200
    mock_service.query.assert_called_once_with(limit=50, status="PENDING")


@patch("app_lib.features.jobs.routes.job_routes._get_sqs_service")
@patch("app_lib.features.jobs.routes.job_routes.job_service")
def test_submit_job(mock_service, mock_sqs_fn, client):
    """Test POST /api/v1/jobs creates a job."""
    mock_sqs = MagicMock()
    mock_sqs.send_message.return_value = "msg-123"
    mock_sqs_fn.return_value = mock_sqs

    resp = client.post(
        "/api/v1/jobs",
        json={"job_type": "passenger_analysis", "input_data": {"ticket": "113803"}},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["job_type"] == "passenger_analysis"
    assert data["input_data"] == {"ticket": "113803"}
    mock_service.save.assert_called_once()
    mock_sqs.send_message.assert_called_once()


def test_submit_job_no_sqs(client):
    """Test POST /api/v1/jobs returns 503 when SQS_QUEUE_URL not set."""
    with patch.dict("os.environ", {}, clear=False):
        # Ensure SQS_QUEUE_URL is not set
        import os

        os.environ.pop("SQS_QUEUE_URL", None)
        resp = client.post(
            "/api/v1/jobs",
            json={"input_data": {"ticket": "113803"}},
        )
        assert resp.status_code == 503
