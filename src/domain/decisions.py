from src.domain.models import DealAssessment, Decision
from src.domain.rules import GOOD_DEAL_MAX_PREMIUM, REVIEW_MAX_PREMIUM, premium_ratio


def assess_deal(estimated_price: float, asking_price: float) -> DealAssessment:
    """The deterministic deal policy: compare a seller's asking price against
    the model's estimate and classify the result.

    This is intentionally kept separate from the price model itself (see
    DECISIONS.md #1): the regression predicts a market price, and this pure,
    rule-based function decides what that price means for the buyer. Asking
    price never influences the price estimate; it is only evaluated here,
    after the estimate has already been produced.
    """
    if estimated_price <= 0 or asking_price <= 0:
        raise ValueError("prices must be positive")
    premium = premium_ratio(asking_price, estimated_price)
    if premium <= GOOD_DEAL_MAX_PREMIUM:
        decision = Decision.GOOD_DEAL
    elif premium <= REVIEW_MAX_PREMIUM:
        decision = Decision.REVIEW
    else:
        decision = Decision.POOR_DEAL
    return DealAssessment(
        estimated_price=round(estimated_price, 2),
        asking_price=round(asking_price, 2),
        difference_amount=round(asking_price - estimated_price, 2),
        difference_percentage=round(premium * 100, 2),
        decision=decision,
    )
