# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""v1 routes for the Fibonacci REST API.

Routes are defined on an APIRouter with prefix="/api/v1".
The router is mounted by the FastAPI app in common/app.py.
"""

import random
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app_lib.features.fibonacci.model.fibonacci_table import FibonacciTable
from app_lib.features.fibonacci.routes.fibonacci_dto import FibonacciResponse
from app_lib.features.fibonacci.service.fibonacci_data_service import (
    FibonacciDataService,
)

router = APIRouter(prefix="/api/v1", tags=["fibonacci"])

data_service = FibonacciDataService()


def _generate_fibonacci_sequence(n: int) -> list[int]:
    """Generate Fibonacci sequence up to F(n).

    Args:
        n: Number of Fibonacci numbers to generate.

    Returns:
        List of Fibonacci numbers from F(1) to F(n).
    """
    if n <= 0:
        return []
    if n == 1:
        return [1]

    fib = [1, 1]
    for i in range(2, n):
        fib.append(fib[i - 1] + fib[i - 2])
    return fib


def _random_fibonacci_value() -> int:
    """Generate a random Fibonacci number between F(1) and F(15).

    Returns:
        A randomly selected Fibonacci number.
    """
    fibonacci_sequence = _generate_fibonacci_sequence(15)
    return random.choice(fibonacci_sequence)


@router.post("/fibonacci", response_model=FibonacciResponse, status_code=201)
def create_fibonacci():
    """Create a new Fibonacci record with a random value."""
    now = datetime.now(timezone.utc).isoformat()
    record = FibonacciTable(
        id=str(uuid.uuid4()),
        value=_random_fibonacci_value(),
        created_at=now,
    )
    data_service.save(record)
    return FibonacciResponse.from_model(record)


@router.get("/fibonacci", response_model=list[FibonacciResponse])
def list_fibonacci(
    limit: int = Query(default=100, ge=1, le=1000),
):
    """List all Fibonacci records, ordered by creation time (newest first)."""
    results = data_service.list(limit=limit)
    # Sort by created_at descending (newest first)
    results.sort(key=lambda r: r.created_at, reverse=True)
    return [FibonacciResponse.from_model(r) for r in results]


@router.get("/fibonacci/{record_id}", response_model=FibonacciResponse)
def get_fibonacci(record_id: str):
    """Get a Fibonacci record by ID."""
    record = data_service.get(record_id)
    if not record:
        raise HTTPException(
            status_code=404, detail=f"Fibonacci record not found: {record_id}"
        )
    return FibonacciResponse.from_model(record)


@router.delete("/fibonacci/{record_id}")
def delete_fibonacci(record_id: str):
    """Delete a Fibonacci record by ID."""
    deleted = data_service.delete(record_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Fibonacci record not found: {record_id}"
        )
    return JSONResponse(content={"deleted": True})
