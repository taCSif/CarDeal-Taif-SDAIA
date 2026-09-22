# Deal-policy thresholds, expressed as a fraction of the estimated price.
# These are application policy constants chosen for this product, not
# statistical properties of the Saudi car market; see DECISIONS.md.
# premium <= GOOD_DEAL_MAX_PREMIUM        -> GOOD_DEAL
# GOOD_DEAL_MAX_PREMIUM < premium <= REVIEW_MAX_PREMIUM -> REVIEW
# premium > REVIEW_MAX_PREMIUM            -> POOR_DEAL
GOOD_DEAL_MAX_PREMIUM = 0.05
REVIEW_MAX_PREMIUM = 0.15


def premium_ratio(asking_price: float, estimated_price: float) -> float:
    """How much the asking price exceeds the model's estimate, as a fraction
    of the estimate. Positive means the seller is asking above the estimated
    market price; negative means asking below it."""
    if estimated_price <= 0:
        raise ValueError("estimated_price must be positive")
    return (asking_price - estimated_price) / estimated_price
