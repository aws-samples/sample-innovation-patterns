# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Data service for Fibonacci records.

Implements AbstractDataService[FibonacciTable] with DynamoDB
as the backing store via PynamoDB. All CRUD operations delegate to
the FibonacciTable PynamoDB model.

Example:
    >>> service = FibonacciDataService()
    >>> record = service.get("abc-123")
    >>> if record:
    ...     print(record.value)
"""

from __future__ import annotations

from typing import Optional

from app_lib.common.data.abstract_data_service import AbstractDataService
from app_lib.features.fibonacci.model.fibonacci_table import FibonacciTable


class FibonacciDataService(AbstractDataService[FibonacciTable]):
    """DynamoDB-backed data service for Fibonacci records.

    Uses FibonacciTable (PynamoDB model) for all persistence
    operations. The id field serves as the primary key.
    """

    def get(self, id: str) -> Optional[FibonacciTable]:
        """Get Fibonacci record by ID.

        Args:
            id: Record ID (hash key).

        Returns:
            Fibonacci record if found, None otherwise.
        """
        try:
            return FibonacciTable.get(id)
        except FibonacciTable.DoesNotExist:
            return None

    def save(self, entity: FibonacciTable) -> None:
        """Save Fibonacci record to DynamoDB.

        Performs an upsert — creates the record if it doesn't exist,
        overwrites it if it does.

        Args:
            entity: FibonacciTable instance to persist.
        """
        entity.save()

    def delete(self, id: str) -> bool:
        """Delete Fibonacci record by ID.

        Args:
            id: Record ID (hash key).

        Returns:
            True if the record was deleted, False if not found.
        """
        item = self.get(id)
        if item:
            item.delete()
            return True
        return False

    def list(self, limit: int = 100) -> list[FibonacciTable]:
        """List Fibonacci records.

        Performs a DynamoDB table scan.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of Fibonacci records.
        """
        return list(FibonacciTable.scan(limit=limit))

    def query(self, limit: int = 100, **filters) -> list[FibonacciTable]:
        """Query Fibonacci records with flexible filters.

        Scans the DynamoDB table and applies filters in-memory.

        Args:
            limit: Maximum number of results.
            **filters: Field filters (e.g., value=5).

        Returns:
            List of records matching all filters.

        Example:
            >>> service.query(value=5)
        """
        records = FibonacciTable.scan(limit=limit)
        if not filters:
            return list(records)
        return [
            r
            for r in records
            if all(getattr(r, k, None) == v for k, v in filters.items())
        ]

    def count(self) -> int:
        """Count total Fibonacci records in the table.

        Returns:
            Total number of Fibonacci records.
        """
        return FibonacciTable.count()
