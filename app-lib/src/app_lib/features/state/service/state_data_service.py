# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Data service for singleton state management.

Implements AbstractDataService[StateTable] with DynamoDB as the backing store.
Provides specialized methods for singleton state operations.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Optional

from app_lib.common.data.abstract_data_service import AbstractDataService
from app_lib.features.state.model.state_table import StateTable

SINGLETON_ID = "current"
VALID_LEVELS = ["low", "mid", "high"]


class StateDataService(AbstractDataService[StateTable]):
    """DynamoDB-backed data service for singleton state management.

    Manages a single state record with a random banded level.
    The state record always uses id="current".
    """

    def get(self, id: str) -> Optional[StateTable]:
        """Retrieve a state record by ID.

        Args:
            id: State record identifier.

        Returns:
            State record if found, None otherwise.
        """
        try:
            return StateTable.get(id)
        except StateTable.DoesNotExist:
            return None

    def save(self, entity: StateTable) -> None:
        """Persist a state entity to DynamoDB.

        Args:
            entity: StateTable instance to persist.
        """
        entity.save()

    def delete(self, id: str) -> bool:
        """Delete a state record by ID.

        Args:
            id: State record identifier.

        Returns:
            True if the record was deleted, False if not found.
        """
        item = self.get(id)
        if item:
            item.delete()
            return True
        return False

    def list(self, limit: int = 100) -> list[StateTable]:
        """List all state records.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of state records (typically contains only one).
        """
        return list(StateTable.scan(limit=limit))

    def query(self, limit: int = 100, **filters) -> list[StateTable]:
        """Query state records with optional filters.

        Args:
            limit: Maximum number of results.
            **filters: Field filters.

        Returns:
            List of state records matching all filters.
        """
        states = StateTable.scan(limit=limit)
        if not filters:
            return list(states)
        return [
            s
            for s in states
            if all(getattr(s, k, None) == v for k, v in filters.items())
        ]

    def count(self) -> int:
        """Count total state records in the table.

        Returns:
            Total number of state records (typically 1).
        """
        return StateTable.count()

    def get_current(self) -> Optional[StateTable]:
        """Get the current singleton state record.

        Returns:
            Current state record if it exists, None otherwise.
        """
        return self.get(SINGLETON_ID)

    def randomize(self) -> StateTable:
        """Randomize the singleton state level.

        Selects a new random level from ["low", "mid", "high"] and
        updates the timestamp. The new value may be the same as the
        previous value.

        Returns:
            Updated state record with new random level.
        """
        now = datetime.now(timezone.utc).isoformat()
        new_level = random.choice(VALID_LEVELS)

        state = StateTable(
            id=SINGLETON_ID,
            level=new_level,
            updated_at=now,
        )
        self.save(state)
        return state

    def initialize_if_missing(self) -> StateTable:
        """Initialize the singleton state if it doesn't exist.

        Returns:
            Existing or newly created state record.
        """
        existing = self.get_current()
        if existing:
            return existing
        return self.randomize()
