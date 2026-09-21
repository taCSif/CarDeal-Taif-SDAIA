from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    GOOD_DEAL = "GOOD_DEAL"
    REVIEW = "REVIEW"
    POOR_DEAL = "POOR_DEAL"


@dataclass(frozen=True)
class Vehicle:
    make: str
    type: str
    year: int
    origin: str
    color: str
    options: str
    engine_size: float
    fuel_type: str
    gear_type: str
    mileage: int
    region: str


@dataclass(frozen=True)
class DealAssessment:
    estimated_price: float
    asking_price: float
    difference_amount: float
    difference_percentage: float
    decision: Decision
