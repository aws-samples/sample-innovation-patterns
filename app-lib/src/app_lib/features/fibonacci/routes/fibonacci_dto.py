# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Pydantic DTOs for the Fibonacci REST API."""

from pydantic import BaseModel, ConfigDict


class FibonacciResponse(BaseModel):
    """Response body for a Fibonacci record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    value: int
    created_at: str

    @classmethod
    def from_model(cls, model) -> "FibonacciResponse":
        """Convert PynamoDB model to response, handling Decimal → int."""
        return cls(
            id=model.id,
            value=int(model.value),
            created_at=model.created_at,
        )
