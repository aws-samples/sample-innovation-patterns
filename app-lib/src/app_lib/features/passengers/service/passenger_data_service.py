# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Data service for Titanic passenger data.

Implements AbstractDataService[TitanicPassengerTable] with DynamoDB
as the backing store via PynamoDB. All CRUD operations delegate to
the TitanicPassengerTable PynamoDB model.

Example:
    >>> service = TitanicPassengerDataService()
    >>> passenger = service.get("24160")
    >>> if passenger:
    ...     print(passenger.name)
"""

from __future__ import annotations

from typing import Optional

from app_lib.common.data.abstract_data_service import AbstractDataService
from app_lib.features.passengers.model.passenger_table import TitanicPassengerTable


class TitanicPassengerDataService(AbstractDataService[TitanicPassengerTable]):
    """DynamoDB-backed data service for Titanic passenger data.

    Uses TitanicPassengerTable (PynamoDB model) for all persistence
    operations. The ticket number serves as the primary key.
    """

    def get(self, id: str) -> Optional[TitanicPassengerTable]:
        """Get passenger by ticket number.

        Args:
            id: Ticket number (hash key).

        Returns:
            Passenger record if found, None otherwise.
        """
        try:
            return TitanicPassengerTable.get(id)
        except TitanicPassengerTable.DoesNotExist:
            return None

    def save(self, entity: TitanicPassengerTable) -> None:
        """Save passenger to DynamoDB.

        Performs an upsert — creates the record if it doesn't exist,
        overwrites it if it does.

        Args:
            entity: TitanicPassengerTable instance to persist.
        """
        entity.save()

    def delete(self, id: str) -> bool:
        """Delete passenger by ticket number.

        Args:
            id: Ticket number (hash key).

        Returns:
            True if the passenger was deleted, False if not found.
        """
        item = self.get(id)
        if item:
            item.delete()
            return True
        return False

    def list(self, limit: int = 100) -> list[TitanicPassengerTable]:
        """List passengers.

        Performs a DynamoDB table scan.

        Args:
            limit: Maximum number of passengers to return.

        Returns:
            List of passenger records.
        """
        return list(TitanicPassengerTable.scan(limit=limit))

    def query(self, limit: int = 100, **filters) -> list[TitanicPassengerTable]:
        """Query passengers with flexible filters.

        Scans the DynamoDB table and applies filters in-memory.
        This is acceptable for the ~1300 record Titanic dataset
        but would not scale to larger tables without GSIs.

        Args:
            limit: Maximum number of results.
            **filters: Field filters (e.g., pclass=1, sex="female", survived=1).

        Returns:
            List of passengers matching all filters.

        Example:
            >>> service.query(pclass=1, survived=1)
            >>> service.query(sex="female", limit=50)
        """
        passengers = TitanicPassengerTable.scan(limit=limit)
        if not filters:
            return list(passengers)
        return [
            p
            for p in passengers
            if all(getattr(p, k, None) == v for k, v in filters.items())
        ]

    def count(self) -> int:
        """Count total passengers in the table.

        Returns:
            Total number of passenger records.
        """
        return TitanicPassengerTable.count()
