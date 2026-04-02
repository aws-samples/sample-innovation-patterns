"""v1 routes for the Titanic passenger REST API.

Routes are defined on an APIRouter with prefix="/api/v1".
The router is mounted by the FastAPI app in common/app.py.

To adapt for your own entity:
1. Replace TitanicPassengerDataService with your data service
2. Replace the Pydantic models from passenger_dto.py
3. Update the route paths and query parameters
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app_lib.features.passengers.model.passenger_table import TitanicPassengerTable
from app_lib.features.passengers.routes.passenger_dto import (
    TitanicPassengerCreate,
    TitanicPassengerResponse,
)
from app_lib.features.passengers.service.passenger_data_service import (
    TitanicPassengerDataService,
)

router = APIRouter(prefix="/api/v1", tags=["passengers"])

data_service = TitanicPassengerDataService()


@router.get("/passengers", response_model=list[TitanicPassengerResponse])
def list_passengers(
    limit: int = Query(default=100, ge=1, le=2000),
    pclass: int | None = Query(default=None),
    survived: int | None = Query(default=None),
    sex: str | None = Query(default=None),
    embarked: str | None = Query(default=None),
):
    """List passengers with optional filters."""
    filters = {
        k: v
        for k, v in {
            "pclass": pclass,
            "survived": survived,
            "sex": sex,
            "embarked": embarked,
        }.items()
        if v is not None
    }
    results = data_service.query(limit=limit, **filters)
    return [TitanicPassengerResponse.from_model(p) for p in results]


# Ticket values can contain slashes (e.g. "SC/AH 29037"), so we use {ticket:path}
# to match across path separators. The frontend encodeURIComponent's the ticket in
# URLs, but servers/proxies decode %2F back to / before FastAPI sees the request.


@router.get("/passengers/{ticket:path}", response_model=TitanicPassengerResponse)
def get_passenger(ticket: str):
    """Get a passenger by ticket number."""
    passenger = data_service.get(ticket)
    if not passenger:
        raise HTTPException(status_code=404, detail=f"Passenger not found: {ticket}")
    return TitanicPassengerResponse.from_model(passenger)


@router.post("/passengers", response_model=TitanicPassengerResponse, status_code=201)
def create_passenger(body: TitanicPassengerCreate):
    """Create a passenger. Upserts if ticket already exists."""
    record = TitanicPassengerTable(**body.model_dump())
    data_service.save(record)
    return TitanicPassengerResponse.from_model(record)


@router.put("/passengers/{ticket:path}", response_model=TitanicPassengerResponse)
def update_passenger(ticket: str, body: TitanicPassengerCreate):
    """Update a passenger by ticket number."""
    existing = data_service.get(ticket)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Passenger not found: {ticket}")
    record = TitanicPassengerTable(**body.model_dump())
    data_service.save(record)
    return TitanicPassengerResponse.from_model(record)


@router.delete("/passengers/{ticket:path}")
def delete_passenger(ticket: str):
    """Delete a passenger by ticket number."""
    deleted = data_service.delete(ticket)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Passenger not found: {ticket}")
    return JSONResponse(content={"deleted": True})
