# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Pydantic DTOs for the background jobs REST API."""

import json

from pydantic import BaseModel


class JobCreate(BaseModel):
    """Request body for submitting a new job."""

    job_type: str = "passenger_analysis"
    input_data: dict  # e.g., {"ticket": "113803"}


class JobResponse(BaseModel):
    """Response body for a job record."""

    job_id: str
    status: str
    job_type: str
    input_data: dict
    metadata: dict | None = None
    error: str | None = None
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, model) -> "JobResponse":
        """Convert JobTable PynamoDB model to response."""
        return cls(
            job_id=model.id,
            status=model.status,
            job_type=model.job_type,
            input_data=json.loads(model.input_data),
            metadata=json.loads(model.metadata) if model.metadata else None,
            error=model.error,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
