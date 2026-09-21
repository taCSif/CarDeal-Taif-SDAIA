from src.domain.models import DealAssessment, Decision
from src.domain.rules import GOOD_DEAL_MAX_PREMIUM, REVIEW_MAX_PREMIUM, premium_ratio


def assess_deal(estimated_price: float, asking_price: float) -> DealAssessment:
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
