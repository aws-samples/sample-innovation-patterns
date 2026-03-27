"""Abstract base class for data services.

Defines a backend-agnostic CRUD interface for entity persistence.
Concrete implementations (DynamoDB, PostgreSQL, in-memory, etc.)
inherit from AbstractDataService[T] and implement all abstract methods.

Example:
    >>> class MyDataService(AbstractDataService[MyModel]):
    ...     def get(self, id: str) -> Optional[MyModel]:
    ...         return MyModel.get(id)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class AbstractDataService(ABC, Generic[T]):
    """Backend-agnostic interface for entity persistence.

    Provides a standard CRUD contract with 6 operations: get, save,
    delete, list, query, and count. Each concrete implementation
    translates these operations to its backing store.

    Type Parameters:
        T: The entity type this data service manages. Can be a PynamoDB
           model, Pydantic model, dataclass, or any Python object.
    """

    @abstractmethod
    def get(self, id: str) -> Optional[T]:
        """Get entity by primary key.

        Args:
            id: Primary key value.

        Returns:
            Entity if found, None otherwise.
        """

    @abstractmethod
    def save(self, entity: T) -> None:
        """Create or update an entity.

        Semantics are upsert — if the entity exists it is overwritten,
        otherwise it is created.

        Args:
            entity: Entity to persist.
        """

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete entity by primary key.

        Args:
            id: Primary key value.

        Returns:
            True if the entity was deleted, False if it was not found.
        """

    @abstractmethod
    def list(self, limit: int = 100) -> list[T]:
        """List entities.

        Args:
            limit: Maximum number of results to return.

        Returns:
            List of entities, up to limit.
        """

    @abstractmethod
    def query(self, limit: int = 100, **filters) -> list[T]:
        """Query entities with filters.

        Filter semantics are implementation-defined. A DynamoDB
        implementation may scan and filter in-memory, while a SQL
        implementation may push filters to WHERE clauses.

        Args:
            limit: Maximum number of results to return.
            **filters: Key-value filters applied to entity attributes.

        Returns:
            List of entities matching all filters.
        """

    @abstractmethod
    def count(self) -> int:
        """Count total entities.

        Returns:
            Total number of entities in the backing store.
        """
