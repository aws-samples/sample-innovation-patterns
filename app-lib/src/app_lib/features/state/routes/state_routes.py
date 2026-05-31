# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""v1 routes for the singleton state REST API.

Routes are defined on an APIRouter with prefix="/api/v1".
The router is mounted by the FastAPI app in common/app.py.
"""

from fastapi import APIRouter, HTTPException

from app_lib.features.state.routes.state_dto import StateResponse
from app_lib.features.state.service.state_data_service import StateDataService

state_router = APIRouter(prefix="/api/v1", tags=["state"])

state_service = StateDataService()


@state_router.get("/state", response_model=StateResponse)
def get_current_state():
    """Get the current singleton state.

    Returns the current state record with its random banded level.
    If no state exists yet, initializes it with a random level.

    Returns:
        Current state record with id, level, and updated_at.
    """
    try:
        state = state_service.initialize_if_missing()
        return StateResponse.from_model(state)
    except Exception as e:
        if "ResourceNotFoundException" in str(e):
            raise HTTPException(
                status_code=503,
                detail="State table not available. Deploy the state table infrastructure.",
            )
        raise


@state_router.post("/state/randomize", response_model=StateResponse)
def randomize_state():
    """Randomize the singleton state level.

    Selects a new random level from ["low", "mid", "high"] and
    updates the timestamp. The new value may be the same as the
    previous value.

    Returns:
        Updated state record with new random level.
    """
    try:
        state = state_service.randomize()
        return StateResponse.from_model(state)
    except Exception as e:
        if "ResourceNotFoundException" in str(e):
            raise HTTPException(
                status_code=503,
                detail="State table not available. Deploy the state table infrastructure.",
            )
        raise
