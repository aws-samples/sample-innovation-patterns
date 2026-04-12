# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Tests for JobTable model."""

from app_lib.features.jobs.model.job_table import JobTable


def test_job_model_attributes():
    """Test job model has correct attributes."""
    job = JobTable(
        id="abc-123",
        status="PENDING",
        job_type="passenger_analysis",
        input_data='{"ticket": "113803"}',
        created_at="2026-04-09T20:00:00+00:00",
        updated_at="2026-04-09T20:00:00+00:00",
    )
    assert job.id == "abc-123"
    assert job.status == "PENDING"
    assert job.job_type == "passenger_analysis"
    assert job.input_data == '{"ticket": "113803"}'
    assert job.created_at == "2026-04-09T20:00:00+00:00"


def test_job_model_nullable_fields():
    """Test job model handles nullable fields."""
    job = JobTable(
        id="abc-123",
        status="PENDING",
        job_type="passenger_analysis",
        input_data="{}",
        created_at="2026-04-09T20:00:00+00:00",
        updated_at="2026-04-09T20:00:00+00:00",
    )
    assert job.metadata is None
    assert job.error is None


def test_job_table_name():
    """Test table name uses PynamodbUtil prefix."""
    assert "jobs" in JobTable.Meta.table_name
