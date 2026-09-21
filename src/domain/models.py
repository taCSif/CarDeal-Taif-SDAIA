from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    GOOD_DEAL = "GOOD_DEAL"
    REVIEW = "REVIEW"
    POOR_DEAL = "POOR_DEAL"


@dataclass(frozen=True)
class Vehicle:
    """User-facing vehicle identity and condition used by the price model."""

    make_model: str
    year: int
    mileage: int


@dataclass(frozen=True)
class DealAssessment:
    estimated_price: float
    asking_price: float
    difference_amount: float
    difference_percentage: float
    decision: Decision
