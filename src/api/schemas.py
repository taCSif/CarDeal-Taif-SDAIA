import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VehicleFields(BaseModel):
    """Shared make_model/year/mileage validation for the four-input contract.

    POST /v1/predict (PredictRequest) and GET /v1/comparables (ComparablesQuery)
    both identify a vehicle the same way; this base keeps that identification
    and its normalization in one place.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    make_model: str = Field(min_length=2, max_length=120)
    year: int = Field(ge=1950, le=2026)
    mileage: int = Field(ge=0, le=2_000_000)

    @field_validator("make_model")
    @classmethod
    def validate_make_model(cls, value: str) -> str:
        # Collapse any run of internal whitespace to a single space so that
        # "Toyota   Camry" and "Toyota Camry" resolve to the same model input.
        # Casing is deliberately preserved to match the dataset's category
        # labels; unseen categories are handled by the encoder at inference.
        value = re.sub(r"\s+", " ", value.strip())
        if not value or len(value.split()) < 2:
            raise ValueError("must contain make and model, for example 'Toyota Camry'")
        return value


class PredictRequest(VehicleFields):
    """Minimal four-input public contract."""

    asking_price: float = Field(gt=0, le=10_000_000)


class ComparablesQuery(VehicleFields):
    """Query parameters for GET /v1/comparables: the same three vehicle fields
    used by PredictRequest, minus asking_price."""


class ComparableCarResponse(BaseModel):
    make_model: str
    year: int
    mileage: int
    price: float


class PredictionData(BaseModel):
    estimated_price: float
    asking_price: float
    difference_amount: float
    difference_percentage: float
    decision: str
    comparable_cars: list[ComparableCarResponse]


class Envelope(BaseModel):
    trace_id: str
    data: Any
