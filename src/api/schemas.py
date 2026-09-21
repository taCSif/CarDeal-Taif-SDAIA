from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    make: str = Field(min_length=1, max_length=80)
    type: str = Field(min_length=1, max_length=120)
    year: int = Field(ge=1950, le=2026)
    origin: str = Field(min_length=1, max_length=40)
    color: str = Field(min_length=1, max_length=40)
    options: str = Field(min_length=1, max_length=40)
    engine_size: float = Field(gt=0, le=15)
    fuel_type: str = Field(min_length=1, max_length=40)
    gear_type: str = Field(min_length=1, max_length=40)
    mileage: int = Field(ge=0, le=2_000_000)
    region: str = Field(min_length=1, max_length=80)
    asking_price: float = Field(gt=0, le=10_000_000)

    @field_validator(
        "make", "type", "origin", "color", "options", "fuel_type", "gear_type", "region"
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class ComparableCarResponse(BaseModel):
    make: str
    type: str
    year: int
    mileage: int
    region: str
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
