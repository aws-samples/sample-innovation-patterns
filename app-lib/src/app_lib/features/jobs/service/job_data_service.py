# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Data service for background jobs.

Implements AbstractDataService[JobTable] with DynamoDB as the backing store.
"""

from __future__ import annotations

from typing import Optional

from app_lib.common.data.abstract_data_service import AbstractDataService
from app_lib.features.jobs.model.job_table import JobTable


class JobDataService(AbstractDataService[JobTable]):
    """DynamoDB-backed data service for background jobs."""

    def get(self, id: str) -> Optional[JobTable]:
        """Retrieve a job by ID."""
        try:
            return JobTable.get(id)
        except JobTable.DoesNotExist:
            return None

    def save(self, entity: JobTable) -> None:
        """Persist a job entity to DynamoDB."""
        entity.save()

    def delete(self, id: str) -> bool:
        """Delete a job by ID."""
        item = self.get(id)
        if item:
            item.delete()
            return True
        return False

    def list(self, limit: int = 100) -> list[JobTable]:
        """List all jobs up to the specified limit."""
        return list(JobTable.scan(limit=limit))

    def query(self, limit: int = 100, **filters) -> list[JobTable]:
        """Query jobs with optional filters."""
        jobs = JobTable.scan(limit=limit)
        if not filters:
            return list(jobs)
        return [
            j for j in jobs if all(getattr(j, k, None) == v for k, v in filters.items())
        ]

    def count(self) -> int:
        """Count total jobs in the table."""
        return JobTable.count()
