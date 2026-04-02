"""Pydantic DTOs for the Titanic passenger REST API."""

import json

from pydantic import BaseModel, ConfigDict, Field


class TitanicPassengerCreate(BaseModel):
    """Request body for creating/updating a passenger."""

    ticket: str
    name: str
    pclass: int = Field(ge=1, le=3)
    survived: int = Field(ge=0, le=1)
    sex: str
    age: float | None = None
    sibsp: int = Field(default=0, ge=0)
    parch: int = Field(default=0, ge=0)
    fare: float | None = None
    cabin: str | None = None
    embarked: str | None = None
    boat: str | None = None
    body: int | None = None
    home_dest: str | None = None
    analysis: str | None = None  # JSON string, set by background jobs


class TitanicPassengerResponse(BaseModel):
    """Response body for a passenger record."""

    model_config = ConfigDict(from_attributes=True)

    ticket: str
    name: str
    pclass: int
    survived: int
    sex: str
    age: float | None = None
    sibsp: int
    parch: int
    fare: float | None = None
    cabin: str | None = None
    embarked: str | None = None
    boat: str | None = None
    body: int | None = None
    home_dest: str | None = None
    analysis: dict | None = None

    @classmethod
    def from_model(cls, model) -> "TitanicPassengerResponse":
        """Convert PynamoDB model to response, handling Decimal → int/float."""
        return cls(
            ticket=model.id,
            name=model.name,
            pclass=int(model.pclass),
            survived=int(model.survived),
            sex=model.sex,
            age=float(model.age) if model.age is not None else None,
            sibsp=int(model.sibsp),
            parch=int(model.parch),
            fare=float(model.fare) if model.fare is not None else None,
            cabin=model.cabin,
            embarked=model.embarked,
            boat=model.boat,
            body=int(model.body) if model.body is not None else None,
            home_dest=model.home_dest,
            analysis=json.loads(model.analysis) if model.analysis else None,
        )
