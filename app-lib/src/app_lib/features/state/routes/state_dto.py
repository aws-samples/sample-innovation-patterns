# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Pydantic DTOs for the state REST API."""

from pydantic import BaseModel, ConfigDict, Field


class StateResponse(BaseModel):
    """Response body for a state record."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="State identifier (always 'current')")
    level: str = Field(description="Random banded level: low, mid, or high")
    updated_at: str = Field(description="ISO 8601 timestamp of last update")

    @classmethod
    def from_model(cls, model) -> "StateResponse":
        """Convert PynamoDB model to response DTO.

        Args:
            model: StateTable instance.

        Returns:
            StateResponse with fields from the model.
        """
        return cls(
            id=model.id,
            level=model.level,
            updated_at=model.updated_at,
        )
