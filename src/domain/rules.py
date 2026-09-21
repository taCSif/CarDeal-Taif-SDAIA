GOOD_DEAL_MAX_PREMIUM = 0.05
REVIEW_MAX_PREMIUM = 0.15


def premium_ratio(asking_price: float, estimated_price: float) -> float:
    if estimated_price <= 0:
        raise ValueError("estimated_price must be positive")
    return (asking_price - estimated_price) / estimated_price
