from dataclasses import dataclass
from enum import StrEnum


# The three possible outcomes of the deterministic deal policy in
# domain.decisions. This is the full set of values the API ever returns for
# "decision"; ordering here is not significant, severity ordering lives in
# domain.rules.
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


# Immutable result of applying the deal policy to a single (estimate, asking
# price) pair. Frozen so a computed assessment can be logged, persisted, or
# compared without risk of being mutated after the fact.
@dataclass(frozen=True)
class DealAssessment:
    estimated_price: float
    asking_price: float
    difference_amount: float
    difference_percentage: float
    decision: Decision
